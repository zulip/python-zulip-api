Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

python tools\test-bots "$args" --coverage
python tools\test-botserver "$args" --coverage combine
python tools\test-zulip "$args" --coverage combine
python tools\test-lib "$args" --coverage combine
