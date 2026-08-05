# Fresh Locked Analysis

- N: 126
- ToolAcc: 0.746
- SchemaValid: 0.921
- SoftArgAcc: 0.744
- E2E: 0.563 [0.476, 0.647]
- Argument field accuracy: 0.744
- Confirmation accuracy: 0.944
- Null status accuracy: 0.367

## Per Group

| name | N | ToolAcc | Schema | ArgExact | Confirm | E2E |
| --- | --- | --- | --- | --- | --- | --- |
| alarm_calendar | 16 | 0.938 | 1.000 | 0.438 | 1.000 | 0.438 |
| camera_media | 16 | 0.812 | 0.938 | 1.000 | 1.000 | 0.812 |
| contacts | 24 | 0.750 | 0.917 | 0.542 | 0.958 | 0.542 |
| files_settings | 20 | 0.650 | 0.850 | 0.650 | 1.000 | 0.550 |
| map_web | 8 | 0.750 | 1.000 | 0.750 | 1.000 | 0.750 |
| message_call | 12 | 0.917 | 0.917 | 0.917 | 0.917 | 0.833 |
| negative_clarification | 30 | 0.600 | 0.900 | 0.667 | 0.833 | 0.367 |

## Per Tool

| name | N | ToolAcc | Schema | ArgExact | Confirm | E2E |
| --- | --- | --- | --- | --- | --- | --- |
| ACTION_CREATE_DOCUMENT | 4 | 0.750 | 0.750 | 0.750 | 1.000 | 0.750 |
| ACTION_EDIT_CONTACT | 4 | 1.000 | 1.000 | 0.500 | 1.000 | 0.500 |
| ACTION_GET_CONTENT | 4 | 0.750 | 1.000 | 0.750 | 1.000 | 0.750 |
| ACTION_GET_RINGTONE | 4 | 0.250 | 0.500 | 0.750 | 1.000 | 0.250 |
| ACTION_IMAGE_CAPTURE | 4 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| ACTION_INSERT_CONTACT | 4 | 0.750 | 1.000 | 0.500 | 0.750 | 0.500 |
| ACTION_INSERT_EVENT | 4 | 1.000 | 1.000 | 0.500 | 1.000 | 0.500 |
| ACTION_OPEN_DOCUMENT | 4 | 0.500 | 1.000 | 0.250 | 1.000 | 0.250 |
| ACTION_PICK | 4 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| ACTION_SET_ALARM | 4 | 0.750 | 1.000 | 0.000 | 1.000 | 0.000 |
| ACTION_SET_TIMER | 4 | 1.000 | 1.000 | 0.250 | 1.000 | 0.250 |
| ACTION_SHOW_ALARMS | 4 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| ACTION_VIDEO_CAPTURE | 4 | 0.750 | 0.750 | 1.000 | 1.000 | 0.750 |
| ACTION_VIEW_CONTACT | 4 | 0.750 | 1.000 | 0.750 | 1.000 | 0.750 |
| INTENT_ACTION_STILL_IMAGE_CAMERA | 4 | 0.750 | 1.000 | 1.000 | 1.000 | 0.750 |
| INTENT_ACTION_VIDEO_CAMERA | 4 | 0.750 | 1.000 | 1.000 | 1.000 | 0.750 |
| dial | 4 | 0.750 | 0.750 | 1.000 | 0.750 | 0.750 |
| get_contact_info | 4 | 0.500 | 0.750 | 0.250 | 1.000 | 0.250 |
| get_contact_info_from_uri | 4 | 0.500 | 0.750 | 0.250 | 1.000 | 0.250 |
| open_settings | 4 | 1.000 | 1.000 | 0.750 | 1.000 | 0.750 |
| search_location | 4 | 0.750 | 1.000 | 0.750 | 1.000 | 0.750 |
| send_email | 4 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| send_message | 4 | 1.000 | 1.000 | 0.750 | 1.000 | 0.750 |
| web_search | 4 | 0.750 | 1.000 | 0.750 | 1.000 | 0.750 |
| NULL:clarification | 15 | 0.400 | 0.867 | 0.533 | 0.733 | 0.333 |
| NULL:unsupported | 15 | 0.800 | 0.933 | 0.800 | 0.933 | 0.400 |

## Fields

| field | N | Accuracy |
| --- | --- | --- |
| DESCRIPTION | 4 | 1.000 |
| EVENT_LOCATION | 1 | 1.000 |
| EXTRA_DAYS | 1 | 0.000 |
| EXTRA_EVENT_ALL_DAY | 1 | 0.000 |
| EXTRA_EVENT_BEGIN_TIME | 4 | 0.500 |
| EXTRA_HOUR | 4 | 0.750 |
| EXTRA_MESSAGE | 5 | 0.000 |
| EXTRA_MINUTES | 4 | 0.750 |
| TITLE | 4 | 1.000 |
| allow_multiple | 2 | 1.000 |
| body | 8 | 1.000 |
| contact_info | 5 | 0.400 |
| contact_uri | 12 | 0.667 |
| data_type | 4 | 1.000 |
| duration | 4 | 1.000 |
| engine | 2 | 1.000 |
| initial_name | 4 | 0.750 |
| key | 8 | 0.625 |
| mime_type | 8 | 0.875 |
| mime_types | 4 | 0.500 |
| name | 4 | 0.250 |
| phone_number | 8 | 1.000 |
| query | 8 | 0.750 |
| setting_type | 4 | 0.750 |
| subject | 4 | 1.000 |
| to | 4 | 1.000 |

## Error Types

| error_type | count |
| --- | --- |
| argument_mismatch | 15 |
| wrong_tool | 15 |
| unsafe_or_unwanted_tool_for_null_request | 12 |
| null_status_mismatch | 7 |
| null_instead_of_tool | 5 |
| schema_invalid | 1 |
