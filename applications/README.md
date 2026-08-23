# applications/

Your job search lives here. **This directory is gitignored** apart from the
example folder, because it names every employer you have approached.

## Layout

```
applications/
  DD.MM.YY/                    the day you prepared it, not a deadline
    NN - Company - Role/       NN is a GLOBAL counter, never restarts per date
      JOB-URL.txt              apply link, location rules, Status:, Applied on:
      NOTES.md                 research notes
      MY-NOTES.md              your own notes, editable from the board
      APPLICATION-ANSWERS.md   screening question answers, if the form had any
      <Name>_Resume.pdf
      <Name>_Cover_Letter.pdf
```

## Why the numbering is global

Numbers are how you refer to a role in conversation and on the command line
(`set_status.py 42 applied`). If they restarted each day you would have five
number 1s and no way to say which you meant.
