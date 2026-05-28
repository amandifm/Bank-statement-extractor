const { Pool } = require('pg');

const pool = new Pool({
  user: 'postgres',
  host: 'localhost',
  database: 'bank_extractor',
  password: '2580',
  port: 5432,
});

async function run() {
  try {
    const res = await pool.query("SELECT COUNT(*) FROM scan_history;");
    console.log("Count:", res.rows[0].count);
    const rows = await pool.query("SELECT * FROM scan_history LIMIT 5;");
    console.log(rows.rows);
  } catch (err) {
    console.error(err);
  } finally {
    pool.end();
  }
}
run();
