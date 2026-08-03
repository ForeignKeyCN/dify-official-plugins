# Trello Trigger

**Author:** langgenius
**Type:** trigger

## Overview

Start Dify workflows from activity on a Trello board. When you add this trigger, Dify registers a **Trello webhook** on the board you select and dispatches an event every time something happens there — a card is created, updated, moved, deleted, commented on, gets an attachment, or a checklist item is added/checked.

## Events

| Event | Trello action | Fires when |
|---|---|---|
| Card Created | `createCard` | a new card is added |
| Card Updated | `updateCard` | a card is renamed / description / due / archived |
| Card Moved | `updateCard` (list move) | a card moves from one list to another |
| Card Deleted | `deleteCard` | a card is deleted |
| Comment Added | `commentCard` | a comment is posted on a card |
| Attachment Added | `addAttachmentToCard` | an attachment is added to a card |
| Checklist Item Created | `createCheckItem` | a checklist item is added |
| Checklist Item State Changed | `updateCheckItemStateOnCard` | a checklist item is checked / unchecked |

Each event outputs the raw Trello webhook payload (`model` = the board, `action` = the activity with its `data`), so your workflow can read card names, list names, member info, comment text, etc.

## Setup

1. Get your **Trello API key** from the [Power-Ups admin portal](https://trello.com/power-ups/admin).
2. Authorize that key to generate an **API token** with read + webhook access.
3. In Dify, add a **Trello Trigger** node, paste the API key and token, and pick the **Board** to watch (the list is fetched from your account).
4. Save — Dify creates the webhook on that board automatically and removes it when you delete the trigger.

## Notes

- One subscription = one webhook on one board. Add multiple triggers to watch multiple boards.
- Trello webhooks do not expire, so no periodic refresh is needed.
- The `Card Moved` event is derived from `updateCard`: it only fires when the card actually changes lists (the payload contains `listBefore` and `listAfter`).

## Privacy

See [PRIVACY.md](PRIVACY.md).
