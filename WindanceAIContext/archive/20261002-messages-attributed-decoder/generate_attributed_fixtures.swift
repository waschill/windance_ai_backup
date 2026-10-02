import Foundation

let cases = [
    ("plain", "Synthetic receipt text."),
    ("unicode", "Synthetic café 😀\nSecond line."),
    ("long", String(repeating: "Synthetic ", count: 200)),
    ("embedded", "prefix EXPECTED suffix"),
    ("empty", "")
]
var output: [[String: Any]] = []
for (name, text) in cases {
    let value = NSAttributedString(string: text)
    let data = NSArchiver.archivedData(withRootObject: value)
    output.append(["name": name, "expected": text, "base64": data.base64EncodedString()])
}
let wrong = NSArchiver.archivedData(withRootObject: "Synthetic plain NSString" as NSString)
output.append(["name": "wrong_root", "expected": NSNull(), "base64": wrong.base64EncodedString()])
let metadata = NSMutableAttributedString(string: "Actual synthetic body")
metadata.addAttribute(NSAttributedString.Key("SyntheticMetadata"), value: "EXPECTED", range: NSRange(location: 0, length: metadata.length))
output.append(["name": "metadata", "expected": "Actual synthetic body", "base64": NSArchiver.archivedData(withRootObject: metadata).base64EncodedString()])
let data = try JSONSerialization.data(withJSONObject: output, options: [.sortedKeys])
print(String(data: data, encoding: .utf8)!)
