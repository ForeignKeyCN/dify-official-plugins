# Privacy Policy

## Data Collection

This plugin does not collect or store personal data of its own. To operate it requires a **Trello API key** and **API token**, which you provide. These are stored and managed by your Dify instance and are used only to authenticate requests to the Trello API.

## Data Processing

To watch a board, the plugin registers a webhook with Trello (via `POST /1/webhooks`) pointing at a callback URL allocated by your Dify instance. When activity occurs on the board, Trello sends the event payload to that callback; the plugin parses it and passes the data to your workflow. The plugin does not retain payloads after they are dispatched. When you delete the trigger, the plugin deletes the webhook from Trello.

## Third-party Services

This plugin communicates with **Trello / Atlassian** (https://trello.com). Your use of Trello is governed by Atlassian's Privacy Policy: https://www.atlassian.com/legal/privacy-policy

## Data Retention

The plugin itself retains no data. Credentials and the webhook subscription record are retained by your Dify instance for as long as the trigger is configured. Board and card data are subject to Trello's own retention policies.

## User Rights

Because the plugin stores no data of its own, requests regarding data access, correction, or deletion should be directed to your Dify administrator (for stored credentials) and to Atlassian/Trello (for data held in your account).

## Contact Information

For privacy-related questions about this plugin, please contact the plugin author via the Dify Marketplace listing.

Last updated: 2026-08-01
