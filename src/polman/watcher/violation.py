# ICOS Dynamic Policy Manager
# Copyright © 2022-2024 Engineering Ingegneria Informatica S.p.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This work has received funding from the European Union's HORIZON research
# and innovation programme under grant agreement No. 101070177.

import logging
import uuid
from polman.common.model import Policy, Violation

from polman.watcher.model import AlertmanagerAlert
from polman.watcher.prometheus_rule_engine import SUBJECT_FIELDS_TO_ICOS_TELEMETRY_LABELS, subject_field_value_from_labels


logger = logging.getLogger(__name__)


def build_violation(alert: AlertmanagerAlert, policy: Policy):

  backend_name = alert.annotations['plm_measurement_backend']
  #backend_status = policy.status.measurementBackends[backend_name]
  
  currentValue = float(alert.annotations['plm_expr_value'])
  threshold = get_threshold(policy, currentValue)
  
  labels = dict(alert.labels)
  
  # delete alertmanager specific label
  del labels['alertname']
  
  # rebuild subject and remove labels that are in the subject
  subject_fields = [k for k in vars(policy.subject).keys() if k != 'type']
  try:
    subject_dict = {k: subject_field_value_from_labels(k, labels) for k in subject_fields}
  except KeyError as ex:
    raise Exception(f'Not enough labels ({ex} is missing) in the alert to build the subject. All the labels mapped to subject fields are required. Modify the query (or modify the dpm implementation?)')
  subject = policy.subject.__class__.model_validate(subject_dict)
  for v in subject_fields:
    del labels[SUBJECT_FIELDS_TO_ICOS_TELEMETRY_LABELS[v]]
  
  return Violation(
    id=str(uuid.uuid4()),
    currentValue=str(currentValue),
    threshold=threshold,
    policyName=policy.name,
    policyId=policy.id,
    measurementBackend=backend_name,
    extraLabels=labels,
    subject=subject
  )

def __get_compare_operator(str):
  if '>' in str:
    return "gt"
  if '<' in str:
    return "lt"
  return None

def __get_sorted_thresholds(thresholds, descending = False):

  th_tuples = [(name, val) for name, val in thresholds.items()]
  
  return sorted(th_tuples, key=lambda tup: tup[1], reverse=descending)

def get_threshold(policy, value):
  
  #
  # TODO: add >= and <= !!!
  #
  
  if not policy.spec.thresholds:
    return None

  compare_operator = None
  if policy.spec.violatedIf:
    compare_operator = __get_compare_operator(policy.spec.violatedIf)
  if not compare_operator:
    compare_operator = __get_compare_operator(policy.spec.expr)
  
  if not compare_operator:
    logger.warn('Cannot determine the compare operator')
    return None
  
  sorted = __get_sorted_thresholds(policy.spec.thresholds, compare_operator == 'gt')
  
  for name, val in sorted:
    if compare_operator == 'gt' and value >= val:
      return name
    if compare_operator == 'lt' and value <= val:
      return name
  
  return '__out_of_range__'