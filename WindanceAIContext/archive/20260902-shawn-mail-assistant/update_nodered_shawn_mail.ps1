param(
    [Parameter(Mandatory=$true)][string]$Token,
    [string]$InputPath = '.\flows.shawn-mail.updated.json'
)
$ErrorActionPreference = 'Stop'
$nodes = Get-Content -Raw $InputPath | ConvertFrom-Json

function Clone-Node([string]$sourceId, [string]$newId) {
    $source = $nodes | Where-Object id -eq $sourceId
    if (-not $source) { throw "Missing source node $sourceId" }
    $clone = ($source | ConvertTo-Json -Depth 100 | ConvertFrom-Json)
    $clone.id = $newId
    return $clone
}

$build = $nodes | Where-Object id -eq 'b25322bfeda8468f'
if (-not $build) { throw 'Missing Herald request builder' }
$build.func = @'
const userText = String(msg.userText || msg.payload || "").trim();
if (!userText) return null;

const senderName = String(msg.senderName || "william");
const isShawn = senderName.toLowerCase() === "shawn";
const isShawnMail = isShawn && (
    /\b(mail|email|inbox|delete|trash|archive|save|keep|draft|mark read)\b/i.test(userText) ||
    /^(yes|no|approve|approved|cancel|no approval)$/i.test(userText)
);

const requestMsg = {...msg};
requestMsg.method = "POST";
requestMsg.headers = { "Content-Type": "application/json" };
if (isShawnMail) {
    requestMsg.url = "http://192.168.36.21:8795/command";
    requestMsg.headers["X-Windance-Internal-Token"] = "__SHAWN_MAIL_TOKEN__";
    requestMsg.payload = { text: userText, user: "Shawn" };
} else {
    requestMsg.url = "http://192.168.36.21:8791/message";
    requestMsg.payload = { message: userText, user: senderName, channel: "max-imessage" };
}
return [null, requestMsg];
'@
$build.func = $build.func.Replace('__SHAWN_MAIL_TOKEN__', $Token)

# Node-RED 5 does not permit msg.url to override a URL configured directly on
# an HTTP Request node. This shared node therefore takes its URL exclusively
# from the routing function above.
$sharedHttp = $nodes | Where-Object id -eq '263dc581f289476a'
if (-not $sharedHttp) { throw 'Missing shared Herald HTTP Request node' }
$sharedHttp.url = ''

$newIds = @('shawn_mail_0750','shawn_mail_1230','shawn_mail_1710','shawn_mail_prepare','shawn_mail_post','shawn_mail_format')
$nodes = @($nodes | Where-Object { $_.id -notin $newIds })

$schedules = @(
    @{id='shawn_mail_0750'; name='7:50 AM Shawn Email Review'; cron='50 07 * * *'; y=800},
    @{id='shawn_mail_1230'; name='12:30 PM Shawn Email Review'; cron='30 12 * * *'; y=840},
    @{id='shawn_mail_1710'; name='5:10 PM Shawn Email Review'; cron='10 17 * * *'; y=880}
)
foreach ($s in $schedules) {
    $n = Clone-Node 'wr_mail_1200' $s.id
    $n.name = $s.name; $n.crontab = $s.cron; $n.x = 160; $n.y = $s.y
    $n.wires = @(, @('shawn_mail_prepare'))
    $nodes += $n
}

$prepare = Clone-Node 'wr_mail_prepare' 'shawn_mail_prepare'
$prepare.name = 'Prepare Shawn email review'; $prepare.x = 430; $prepare.y = 840
$prepare.func = @'
msg.method="POST";
msg.url="http://192.168.36.21:8795/report";
msg.headers={"Content-Type":"application/json","X-Windance-Internal-Token":"__TOKEN__"};
msg.payload="";
return msg;
'@
$prepare.func = $prepare.func.Replace('__TOKEN__', $Token)
$prepare.wires = @(, @('shawn_mail_post'))
$nodes += $prepare

$post = Clone-Node 'wr_mail_post' 'shawn_mail_post'
$post.name = 'Shawn Mail Assistant /report'; $post.x = 700; $post.y = 840
$post.url = 'http://192.168.36.21:8795/report'
$post.wires = @(, @('shawn_mail_format'))
$nodes += $post

$format = Clone-Node 'wr_mail_format' 'shawn_mail_format'
$format.name = 'Format Shawn email review'; $format.x = 980; $format.y = 840
$format.func = @'
const res = msg.payload || {};
if (Number(msg.statusCode || 200) >= 400 || !res.reply) {
    msg.payload = "Shawn Email Review could not be prepared. Iris logged the failure for repair.";
} else {
    msg.payload = String(res.reply).trim();
}
msg.recipient = "+16054403400";
return msg;
'@
$format.wires = @(, @('wr_train_send'))
$nodes += $format

$nodes | ConvertTo-Json -Depth 100 -Compress | Set-Content -Encoding utf8NoBOM $InputPath
