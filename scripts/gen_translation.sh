xgettext -o locales/templates/maplebot.pot src/*.py
# msginit -i locales/maplebot.pot -o locales/zh_TW/LC_MESSAGES/maplebot.po
msgmerge -U locales/zh_TW/LC_MESSAGES/maplebot.po locales/templates/maplebot.pot
msgfmt locales/zh_TW/LC_MESSAGES/maplebot.po -o locales/zh_TW/LC_MESSAGES/maplebot.mo