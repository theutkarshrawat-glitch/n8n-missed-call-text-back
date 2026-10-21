import json, uuid
def nid(): return str(uuid.uuid4())
TW={"twilioApi":{"id":"REPLACE_TWILIO","name":"Twilio account"}}
GS={"googleSheetsOAuth2Api":{"id":"REPLACE_GSHEETS","name":"Google Sheets account"}}
OA={"httpHeaderAuth":{"id":"REPLACE_OPENAI","name":"OpenAI (Authorization: Bearer sk-...)"}}
TWIML='<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
nodes=[
 {"parameters":{"content":"## Missed-call AI text-back\nFlow A: Twilio call status webhook. If the call was not answered, text the caller back within seconds and log the lead.\nFlow B: Twilio inbound SMS webhook. An LLM qualifies the reply (service, urgency), every lead gets a reply with the booking link, urgent leads also trigger an owner SMS alert, and every reply is logged to the CRM sheet.\n\nSetup: set BUSINESS_NAME, BOOKING_URL and OWNER_PHONE in the Config nodes, connect Twilio, Google Sheets and an OpenAI header credential, then point your Twilio number's status callback to /missed-call and its messaging webhook to /sms-reply.","height":300,"width":520},"id":nid(),"name":"About this workflow","type":"n8n-nodes-base.stickyNote","typeVersion":1,"position":[-260,-380]},
 # Flow A
 {"parameters":{"httpMethod":"POST","path":"missed-call","responseMode":"responseNode","options":{}},"id":nid(),"name":"Twilio Call Status","type":"n8n-nodes-base.webhook","typeVersion":2,"position":[0,0],"webhookId":nid()},
 {"parameters":{"assignments":{"assignments":[
   {"id":nid(),"name":"BUSINESS_NAME","value":"Bright Smile Dental","type":"string"},
   {"id":nid(),"name":"caller","value":"={{ $json.body.From }}","type":"string"},
   {"id":nid(),"name":"business_number","value":"={{ $json.body.To }}","type":"string"},
   {"id":nid(),"name":"call_status","value":"={{ $json.body.CallStatus || $json.body.DialCallStatus }}","type":"string"}]},"options":{}},
  "id":nid(),"name":"Config + Parse Call","type":"n8n-nodes-base.set","typeVersion":3.4,"position":[220,0]},
 {"parameters":{"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"loose"},"conditions":[
   {"id":nid(),"leftValue":"={{ ['no-answer','busy','failed','canceled'].includes($json.call_status) }}","rightValue":True,"operator":{"type":"boolean","operation":"true","singleValue":True}}],"combinator":"and"},"options":{}},
  "id":nid(),"name":"Missed?","type":"n8n-nodes-base.if","typeVersion":2,"position":[440,0]},
 {"parameters":{"from":"={{ $json.business_number }}","to":"={{ $json.caller }}","message":"=Hi, this is {{ $json.BUSINESS_NAME }}. Sorry we missed your call! What can we help you with today? Reply here and we'll get you booked in."},
  "id":nid(),"name":"Text Caller Back","type":"n8n-nodes-base.twilio","typeVersion":1,"position":[660,-100],"credentials":TW},
 {"parameters":{"operation":"append","documentId":{"__rl":True,"value":"REPLACE_SHEET_ID","mode":"id"},"sheetName":{"__rl":True,"value":"Leads","mode":"name"},
   "columns":{"mappingMode":"defineBelow","value":{"timestamp":"={{ $now.toISO() }}","phone":"={{ $('Config + Parse Call').item.json.caller }}","event":"missed_call","status":"texted_back"},"matchingColumns":[],"schema":[]},"options":{}},
  "id":nid(),"name":"Log Missed Call (CRM)","type":"n8n-nodes-base.googleSheets","typeVersion":4.5,"position":[880,-100],"credentials":GS},
 {"parameters":{"respondWith":"text","responseBody":TWIML,"options":{"responseHeaders":{"entries":[{"name":"Content-Type","value":"text/xml"}]}}},
  "id":nid(),"name":"Ack Twilio (call)","type":"n8n-nodes-base.respondToWebhook","typeVersion":1.1,"position":[1100,0]},
 # Flow B
 {"parameters":{"httpMethod":"POST","path":"sms-reply","responseMode":"responseNode","options":{}},"id":nid(),"name":"Twilio Inbound SMS","type":"n8n-nodes-base.webhook","typeVersion":2,"position":[0,400],"webhookId":nid()},
 {"parameters":{"assignments":{"assignments":[
   {"id":nid(),"name":"BUSINESS_NAME","value":"Bright Smile Dental","type":"string"},
   {"id":nid(),"name":"BOOKING_URL","value":"https://cal.com/your-business/appointment","type":"string"},
   {"id":nid(),"name":"OWNER_PHONE","value":"+15550000000","type":"string"},
   {"id":nid(),"name":"lead_phone","value":"={{ $json.body.From }}","type":"string"},
   {"id":nid(),"name":"business_number","value":"={{ $json.body.To }}","type":"string"},
   {"id":nid(),"name":"message","value":"={{ $json.body.Body }}","type":"string"}]},"options":{}},
  "id":nid(),"name":"Config + Parse SMS","type":"n8n-nodes-base.set","typeVersion":3.4,"position":[220,400]},
 {"parameters":{"method":"POST","url":"https://api.openai.com/v1/chat/completions","authentication":"genericCredentialType","genericAuthType":"httpHeaderAuth","sendBody":True,"specifyBody":"json",
   "jsonBody":"={{ JSON.stringify({ model: 'gpt-4o-mini', response_format: { type: 'json_object' }, temperature: 0, messages: [ { role: 'system', content: 'You qualify inbound leads for ' + $json.BUSINESS_NAME + '. Read the customer text and return JSON with keys: service (short string), urgency (one of: urgent, soon, browsing), summary (one sentence), reply (a friendly SMS under 300 characters that answers them and invites them to book). Never invent prices or availability.' }, { role: 'user', content: $json.message } ] }) }}","options":{}},
  "id":nid(),"name":"AI Qualify Lead","type":"n8n-nodes-base.httpRequest","typeVersion":4.2,"position":[440,400],"credentials":OA},
 {"parameters":{"jsCode":"const cfg = $('Config + Parse SMS').first().json;\nlet q = {};\ntry { q = JSON.parse($json.choices[0].message.content); } catch (e) { q = {}; }\nconst urgency = ['urgent','soon','browsing'].includes(q.urgency) ? q.urgency : 'soon';\nconst reply = (q.reply || `Thanks for your message! You can book a time here:`) + ` Book here: ${cfg.BOOKING_URL}`;\nreturn [{ json: { ...cfg, service: q.service || 'unknown', urgency, summary: q.summary || cfg.message, reply } }];"},
  "id":nid(),"name":"Parse AI Result","type":"n8n-nodes-base.code","typeVersion":2,"position":[660,400]},
 {"parameters":{"from":"={{ $json.business_number }}","to":"={{ $json.lead_phone }}","message":"={{ $json.reply }}"},
  "id":nid(),"name":"Send Reply + Booking Link","type":"n8n-nodes-base.twilio","typeVersion":1,"position":[880,400],"credentials":TW},
 {"parameters":{"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"loose"},"conditions":[
   {"id":nid(),"leftValue":"={{ $('Parse AI Result').item.json.urgency }}","rightValue":"urgent","operator":{"type":"string","operation":"equals"}}],"combinator":"and"},"options":{}},
  "id":nid(),"name":"Urgent?","type":"n8n-nodes-base.if","typeVersion":2,"position":[1100,400]},
 {"parameters":{"from":"={{ $('Parse AI Result').item.json.business_number }}","to":"={{ $('Parse AI Result').item.json.OWNER_PHONE }}","message":"=URGENT lead {{ $('Parse AI Result').item.json.lead_phone }}: {{ $('Parse AI Result').item.json.summary }}"},
  "id":nid(),"name":"Alert Owner","type":"n8n-nodes-base.twilio","typeVersion":1,"position":[1320,300],"credentials":TW},
 {"parameters":{"operation":"append","documentId":{"__rl":True,"value":"REPLACE_SHEET_ID","mode":"id"},"sheetName":{"__rl":True,"value":"Leads","mode":"name"},
   "columns":{"mappingMode":"defineBelow","value":{"timestamp":"={{ $now.toISO() }}","phone":"={{ $('Parse AI Result').item.json.lead_phone }}","event":"sms_reply","status":"={{ $('Parse AI Result').item.json.urgency }}","service":"={{ $('Parse AI Result').item.json.service }}","summary":"={{ $('Parse AI Result').item.json.summary }}"},"matchingColumns":[],"schema":[]},"options":{}},
  "id":nid(),"name":"Log Lead (CRM)","type":"n8n-nodes-base.googleSheets","typeVersion":4.5,"position":[1540,400],"credentials":GS},
 {"parameters":{"respondWith":"text","responseBody":TWIML,"options":{"responseHeaders":{"entries":[{"name":"Content-Type","value":"text/xml"}]}}},
  "id":nid(),"name":"Ack Twilio (sms)","type":"n8n-nodes-base.respondToWebhook","typeVersion":1.1,"position":[1760,400]},
]
def c(*targets): return {"main":[[{"node":t,"type":"main","index":0} for t in targets]]}
conn={
 "Twilio Call Status":c("Config + Parse Call"),
 "Config + Parse Call":c("Missed?"),
 "Missed?":{"main":[[{"node":"Text Caller Back","type":"main","index":0}],[{"node":"Ack Twilio (call)","type":"main","index":0}]]},
 "Text Caller Back":c("Log Missed Call (CRM)"),
 "Log Missed Call (CRM)":c("Ack Twilio (call)"),
 "Twilio Inbound SMS":c("Config + Parse SMS"),
 "Config + Parse SMS":c("AI Qualify Lead"),
 "AI Qualify Lead":c("Parse AI Result"),
 "Parse AI Result":c("Send Reply + Booking Link"),
 "Send Reply + Booking Link":c("Urgent?"),
 "Urgent?":{"main":[[{"node":"Alert Owner","type":"main","index":0}],[{"node":"Log Lead (CRM)","type":"main","index":0}]]},
 "Alert Owner":c("Log Lead (CRM)"),
 "Log Lead (CRM)":c("Ack Twilio (sms)"),
}
names={n["name"] for n in nodes}
for k,v in conn.items():
    assert k in names,k
    for br in v["main"]:
        for t in br: assert t["node"] in names,t
wf={"name":"Missed-Call AI Text-Back (Lead Recovery)","nodes":nodes,"connections":conn,"active":False,"settings":{"executionOrder":"v1"},"pinData":{},"tags":[]}
json.dump(wf,open("missed-call-text-back.n8n.json","w"),indent=2)
print("ok",len(nodes))
