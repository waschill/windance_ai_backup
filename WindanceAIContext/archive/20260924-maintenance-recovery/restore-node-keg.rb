require "keg"
require "keg_relocate"
keg = Keg.new(Pathname.new("/opt/homebrew/Cellar/node/26.8.1"))
keg.replace_placeholders_with_locations(nil)
puts "Rollback keg relocated using Homebrew"
