const express = require('express');
const fs = require('fs');
const path = '/data/storage.log';
const app = express();

app.use(express.text({ type: 'text/plain', limit: '1mb' }));
app.use(express.json()); // for /migrate JSON body

// Append log entry
app.post('/log', (req, res) => {
  const txt = req.body || "";
  fs.appendFile(path, txt + "\n", (err) => {
    if (err) {
      res.status(500).send('error');
    } else {
      res.status(200).send('');
    }
  });
});

// Read full log
app.get('/log', (req, res) => {
  fs.readFile(path, 'utf8', (err, data) => {
    if (err) {
      res.set('Content-Type', 'text/plain').send('');
    } else {
      res.set('Content-Type', 'text/plain').send(data);
    }
  });
});

// Reset log /truncate file
app.post('/reset', (req, res) => {
  fs.writeFile(path, "", (err) => {
    if (err) {
      res.status(500).send('error');
    } else {
      res.status(200).send('OK');
    }
  });
});

/*
  Migration endpoint:
  POST /migrate
  JSON body: { "to": "v1.0" }  -> convert minutes -> hours (for old v1.0)
             { "to": "v1.1" }  -> convert hours -> minutes (for new v1.1)

  The migration detects lines containing "uptime <num> hours" or "uptime <num> minutes"
  and converts them accordingly. Other lines are left unchanged.

  Response: JSON with summary { migrated: <n>, total_lines: <m>, to: "<v1.1|v1.0>" }
*/
app.post('/migrate', (req, res) => {
  const body = req.body || {};
  const to = body.to || (typeof req.body === 'string' ? JSON.parse(req.body).to : undefined);

  if (!to || (to !== 'v1.0' && to !== 'v1.1')) {
    return res.status(400).json({ error: "invalid 'to' version; use 'v1.0' or 'v1.1'" });
  }

  fs.readFile(path, 'utf8', (err, data) => {
    // If file doesn't exist, treat as empty
    const content = err ? "" : data;
    if (!content) {
      // create empty file if not exists
      fs.writeFile(path, "", { flag: 'a' }, (we) => {
        if (we) {
          return res.status(500).json({ error: "failed to create storage file" });
        } else {
          return res.json({ migrated: 0, total_lines: 0, to: to });
        }
      });
      return;
    }

    const lines = content.split(/\r?\n/);
    let migrated = 0;
    const outLines = lines.map((ln) => {
      if (!ln || ln.trim() === "") return ln;

      // Try to find 'uptime <number> hours' or 'uptime <number> minutes'
      // We'll accept decimal numbers
      const hoursMatch = ln.match(/uptime\s+([0-9]+(?:\.[0-9]+)?)\s+hours/);
      const minutesMatch = ln.match(/uptime\s+([0-9]+(?:\.[0-9]+)?)\s+minutes/);

      if (to === 'v1.1') {
        // convert hours -> minutes
        if (hoursMatch) {
          const hours = parseFloat(hoursMatch[1]);
          const minutes = +(hours * 60).toFixed(2);
          migrated++;
          return ln.replace(/uptime\s+[0-9]+(?:\.[0-9]+)?\s+hours/, `uptime ${minutes} minutes`);
        }
        // if already minutes, leave as-is
        return ln;
      } else {
        // to === 'v1.0' convert minutes -> hours
        if (minutesMatch) {
          const minutes = parseFloat(minutesMatch[1]);
          const hours = +(minutes / 60).toFixed(2);
          migrated++;
          return ln.replace(/uptime\s+[0-9]+(?:\.[0-9]+)?\s+minutes/, `uptime ${hours} hours`);
        }
        // if already hours, leave as-is
        return ln;
      }
    });

    const tmpPath = path + ".tmp";
    fs.writeFile(tmpPath, outLines.join("\n"), 'utf8', (we) => {
      if (we) {
        return res.status(500).json({ error: "failed to write migrated file" });
      }
      fs.rename(tmpPath, path, (re) => {
        if (re) {
          return res.status(500).json({ error: "failed to replace storage file" });
        }
        const total_lines = lines.filter(l => l && l.trim() !== "").length;
        return res.json({ migrated: migrated, total_lines: total_lines, to: to });
      });
    });
  });
});

const port = 8200;
app.listen(port, '0.0.0.0', () => {
  console.log(`Storage listening on ${port}`);
});
