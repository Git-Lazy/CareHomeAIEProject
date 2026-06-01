# Launch the CareHome app using the project's virtual environment.
# Works regardless of where it's invoked from ($PSScriptRoot = this file's folder).
Set-Location -Path $PSScriptRoot
& "$PSScriptRoot\.venv\Scripts\python.exe" app.py
