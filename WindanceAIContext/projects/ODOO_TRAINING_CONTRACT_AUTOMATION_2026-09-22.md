# Odoo customer form to training contract — 2026-09-22

Status: REPAIRED, DELIVERY-VERIFIED AND PUBLISHED. William authorized repair
of the form-to-contract workflow and separation of Odoo system aliases from his
personal signing address. No agreement was signed by the agent.

## Verified findings

The earlier conversation, `Create Odoo Customer Form`, left automation 32
(`Send Training Agreement - New Customer`) active with code action 2183
(`Send Horse Training Contract`). The website form creates `res.partner` records
with hidden checked `x_studio_training_customer`. Its page is 190, view 10814,
key `website.registration-1`, URL `/registration-1`, website Windance Farms.
The page was unpublished at inspection.

William subsequently requested the one-word name **Intake** and explicitly
authorized publication. Page title, visible heading and navigation entry now
read Intake, with URL `https://www.windance.farm/intake`. Original heading styling
is preserved. Page 190 is published; a signed-out browser view confirmed its
title, Intake heading, form and Submit button on the public domain.

Actual Odoo version is SaaS 19.3 Enterprise. The action's wizard/role fields exist;
the earlier suspicion of guessed invalid field names was not confirmed. A
transaction that executed the native Sign creation method, with email disabled,
reproduced: "This email address is already used as a mail alias and cannot be
used for signing." The existing personal address was simultaneously the
reflectsody.com domain's catchall, bounce and default-from address.

William correctly reported that this address had worked before. A September 20
completed agreement used the same email. The alias-domain record's last pre-repair
edit was August 2. The historical cause of the changed behavior is not established;
do not claim a confirmed SaaS upgrade regression or user-caused recent change.

## Changes

Only alias-domain record 6 (`reflectsody.com`) was changed:

| Setting | New local part |
|---|---|
| Catchall | `william+odoo-replies` |
| Bounce | `william+odoo-bounces` |
| Default From | `william+odoo-notifications` |

These are tags on the existing Google Workspace mailbox, not new accounts.
William's contact/user email, SMTP credentials, domains, DNS and other alias-domain
records are unchanged. A single message addressed to all three tagged addresses
was accepted by Odoo SMTP and independently found in William's Gmail Inbox.
Windance Farms and Reflectsody share alias-domain 6; both now use the separated
system addresses. Other company alias domains retain their preexisting settings.

Code action 2183 now uses template 57's actual Signer 1/Signer 2 roles, customer
as signer 1, William's existing contact 3 as signer 2, and explicit signing order
1 then 2. It uses Odoo's native signature wizard under the template owner's
existing user (2), links the resulting request to its contact, and skips an
existing non-canceled request for the same contact/template. The template PDF,
legal terms and signature fields were not edited. Automation scope remains
On create + Training Customer set. Existing contacts are not bulk processed.

The previous action assigned both signers order 1. The repaired order follows
the original requested workflow: customer signs first, owner countersigns second.
Missing configuration/contact email yields an explicit failure, not a false
claim of sending. This remains a synchronous Odoo transaction; a future Sign
failure can still roll back the form submission. No retry queue was introduced.

## Verification

- Several diagnostic transactions deliberately rolled back every test record and
  temporary alias value. `no_sign_mail` disabled email. No real customer was used.
- Separating all three reserved addresses removed the reproduced rejection;
  changing only catchall/bounce, or only default-from, did not.
- Candidate execution twice produced one linked request, signer roles 7/8 in
  order 1/2, and zero new mail records during the no-mail test.
- A website-style public-user/sudo contact creation triggered the candidate
  automation successfully in a rolled-back transaction.
- The real authenticated browser submitted a clearly labeled synthetic customer
  through `/registration-1`, using William's normal mailbox. It reached the
  thank-you page, created contact 2666, and generated request 128 automatically.
- Gmail independently confirmed arrival of the training signature request from
  William's normal address to that same address. No alternate personal address
  was required. Re-running action 2183 on the test contact created no duplicate.
- The unsigned test request was canceled through Odoo's native `cancel` method,
  and its test contact was archived. Neither signer signed. Actual second-stage
  email after a customer signature was not tested by accepting a legal agreement.
- Automation remains enabled, original trigger/domain preserved. Following the
  owner's explicit publication request, the renamed Intake form is public.

An existing incoming IMAP server is configured but in draft state. This repair
verified delivery to the existing Gmail mailbox; it does not claim to activate
inbound chatter synchronization or repair all historical email routing.

## Use

Send customers `https://www.windance.farm/intake`.
They enter contact/horse details; successful submission creates the contact and
emails the Horse Training Contract for signing. William uses his existing email
for countersignature. Do not sign the canceled test request. The form's current
generic thank-you message was not changed.

## Recovery and evidence

Private source snapshots, schema checks and receipts live on HERALD at
`/Users/herald/services/odoo-contract-repair-20260922`. Do not publish raw customer
data, email contents, signature URLs/tokens, credentials or database exports.

`automation-before.json` contains the original rule/code; `mail-alias-before.json`
contains the selected original alias fields. `form-views-before.json` records the
original form view. `page-before-rename.json` and `menu-before-rename.json` preserve
the earlier page/navigation values; `published-page.json` records publication.
`training_agreement_action.py` is the deployed source with
SHA-256 `74e35a38011f1906eca42b291898cf77d4c074b77db8f8a6c568e3fd5d45d076`.
`live-form-receipt.json`, `final-verification.json`, the diagnostic verification
files and `routing-test-mail.json` preserve checks. Temporary diagnostic server
action 2189 is unbound and neutralized to `action = False`.

Rollback only the selected alias fields and action code if required; verify
current values before restoration. Restoring the old combination will restore
the reproduced Sign failure. Preserve contract history and do not replay old
form submissions. Retain the archived test contact and canceled test request as
evidence rather than deleting business records. No Training Schedule, SyncThing,
Level 8, credential, or unrelated customer-record change was made.
