# TEQUILA Logs Directory

This directory contains generation logs, retry attempts, and invalid responses for debugging.

## Structure
- `Week{XX}_Day{Y}_retries.log` - Retry attempt logs
- `invalid_responses/` - Invalid LLM responses saved for debugging

## Usage
Logs are automatically created during generation when retries occur or validation fails.
Review these logs to diagnose issues with LLM generation.
