from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.graph_client import GraphAuthError, context_for, graph_request, require
from tools.outputs import with_outputs
from tools.sheet_rows import UsedRange, parse_records, rows_for_header


class UpsertRowsTool(Tool):
    """
    Update the rows whose key column matches, append the others (n8n: Worksheet > Append or
    Update). Rows are objects keyed by the header row; columns left out of an object keep
    their current value.
    """

    @with_outputs
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            workbook_id, worksheet_name, key_column = require(tool_parameters, "workbook_id", "worksheet_name", "key_column")
            records = parse_records(tool_parameters.get("rows"))
            if not isinstance(records[0], dict):
                raise GraphAuthError('rows must be objects keyed by column header, e.g. [{"ID": "42", "Status": "Done"}].')
            ctx = context_for(self, tool_parameters)
            used = UsedRange(ctx, workbook_id, worksheet_name)
            if used.empty:
                raise GraphAuthError(f"'{worksheet_name}' has no header row; add one, or use the append tool.")
            header = [str(h) for h in used.header]
            if key_column not in header:
                raise GraphAuthError(f"'{key_column}' is not a column header. Headers: {', '.join(header)}.")
            key_at = header.index(key_column)
            if any(str(r.get(key_column, "")).strip() == "" for r in records):
                raise GraphAuthError(f"Every row needs a value for the key column '{key_column}'.")
            rows_for_header(records, header)  # rejects keys that are not headers

            # Sheet row number of each existing key (the first one wins, like n8n).
            where: dict[str, int] = {}
            for i, row in enumerate(used.rows):
                where.setdefault(str(row[key_at]) if key_at < len(row) else "", used.first_row + 1 + i)
            current = {used.first_row + 1 + i: list(row) + [""] * (len(header) - len(row)) for i, row in enumerate(used.rows)}

            updated, appended = 0, []
            next_row = used.next_row()
            for record in records:
                key = str(record[key_column])
                row_number = where.get(key)
                cells = list(current.get(row_number, [""] * len(header)) if row_number else [""] * len(header))
                merged = rows_for_header([record], header)[0]
                for col, name in enumerate(header):
                    if name in record:
                        cells[col] = merged[col]
                if row_number:
                    updated += 1
                else:
                    row_number, next_row = next_row, next_row + 1
                    where[key] = row_number
                    appended.append(key)
                current[row_number] = cells
                graph_request(
                    ctx, "PATCH", ctx.range(workbook_id, worksheet_name, used.address(row_number, len(header))),
                    json_body={"values": [cells]},
                )
        except GraphAuthError as e:
            yield self.create_text_message(f"Failed to update or append rows: {e}")
            return

        self._out.update(rows_updated=updated, rows_appended=len(appended), success=True)
        yield self.create_text_message(
            f"In '{worksheet_name}': updated {updated} row(s) and appended {len(appended)} matching on '{key_column}'."
        )
        yield self.create_json_message({"rows_updated": updated, "rows_appended": len(appended), "appended_keys": appended})
