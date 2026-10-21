# Missed-Call AI Text-Back (n8n workflow)

An n8n workflow for small service businesses: when a call is missed, it texts the caller back automatically,
then uses AI to qualify their reply and send a booking link.

Live demo (web page showing the lead-recovery concept): https://theutkarshrawat-glitch.github.io/lead-recovery-demo/

## What it does

**Flow A – missed call** (`POST /missed-call`, Twilio call status callback)
- If the call status is `no-answer`, `busy`, `failed` or `canceled`, text the caller back from the business number via Twilio.
- Log the lead to a Google Sheet (`Leads` tab).

**Flow B – SMS reply** (`POST /sms-reply`, Twilio messaging webhook)
- Send the caller's reply to OpenAI (`gpt-4o-mini`, JSON output) to get `service`, `urgency` (urgent / soon / browsing), a one-line summary and a short reply.
- Text that reply plus the booking link back to the lead.
- If urgency is `urgent`, SMS an alert to the owner.
- Log the lead (service, urgency, summary) to the Google Sheet.

## Node flow

```
A: Twilio Call Status -> Config + Parse Call -> Missed? -> Text Caller Back -> Log Missed Call (CRM) -> Ack Twilio (call)
                                                    \-- (not missed) -----------------------------------> Ack Twilio (call)

B: Twilio Inbound SMS -> Config + Parse SMS -> AI Qualify Lead -> Parse AI Result -> Send Reply + Booking Link
   -> Urgent? -> Alert Owner -> Log Lead (CRM) -> Ack Twilio (sms)
            \-- (not urgent) -> Log Lead (CRM)
```

## Import into n8n

1. In n8n: **Workflows > Import from File** and pick `missed-call-text-back.n8n.json`.
2. Create and attach credentials (the file contains placeholders only):
   - **Twilio** (Account SID + Auth Token) on the three Twilio nodes.
   - **OpenAI**: an HTTP **Header Auth** credential, `Authorization: Bearer <your key>`, on "AI Qualify Lead".
   - **Google Sheets** (OAuth2) on the two Sheets nodes.
3. Replace `REPLACE_SHEET_ID` in both Sheets nodes. Sheet columns: `timestamp, phone, event, status, service, summary`.
4. Set `BUSINESS_NAME`, `BOOKING_URL` and `OWNER_PHONE` in the two Config nodes.
5. Activate, then point your Twilio number's call status callback to `/webhook/missed-call` and its messaging webhook to `/webhook/sms-reply`.

`build.py` regenerates the JSON from Python if you want to change it in code.

## Status

The workflow JSON imports into n8n. It has **not yet been run end to end** with live Twilio, OpenAI or
Google Sheets accounts, so expect to adjust details (field mapping, phone formats) on first real run.

## License

MIT
