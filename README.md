# Minimal Patient Data Viewer — New Sheet + Not Found Handling

Default CSV:

`https://docs.google.com/spreadsheets/d/1lKKAgJMcpIt2F6E2SJJJYCxybAV2l_Cli1Jb-LzlSkA/export?format=csv&gid=0`

Usage:
- Normal: `?row=5`
- Locked: `?row=5&lock=1`
- By ID: `?id=ABC123&id_col=PatientID&lock=1`
- Not found messages shown if row out of range or ID not matched.

Override to other tabs via `?sheet_id=<ID>&gid=<GID>` when not locked.
