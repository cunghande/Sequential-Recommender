import bcrypt from "bcryptjs"
import mysql from "mysql2/promise"

const DEFAULT_PASSWORD = "123456"
const passwordHash = bcrypt.hashSync(DEFAULT_PASSWORD, 10)

const connection = await mysql.createConnection({
  host: "127.0.0.1",
  user: "root",
  password: "cunghande",
  database: "recommendation_db",
})

await connection.execute(`
  UPDATE users
  SET email = CONCAT('user', user_id, '@demo.local')
  WHERE email IS NULL OR email = ''
`)

await connection.execute(
  `
  UPDATE users
  SET password_hash = ?
  WHERE password_hash IS NULL OR password_hash = ''
  `,
  [passwordHash],
)

const demoUsers = [
  ["demo", "demo@example.com", "Demo User"],
  ["1001", "user1001@example.com", "User 1001"],
  ["1002", "user1002@example.com", "User 1002"],
  ["1003", "user1003@example.com", "User 1003"],
]

for (let id = 1; id <= 20; id += 1) {
  demoUsers.push([String(id), `dataset${id}@demo.local`, `Dataset User ${id}`])
}

for (const [userId, email, fullName] of demoUsers) {
  await connection.execute(
    `
    INSERT INTO users (user_id, email, full_name, password_hash)
    VALUES (?, ?, ?, ?)
    ON DUPLICATE KEY UPDATE
      email = COALESCE(NULLIF(email, ''), VALUES(email)),
      full_name = COALESCE(NULLIF(full_name, ''), VALUES(full_name)),
      password_hash = COALESCE(NULLIF(password_hash, ''), VALUES(password_hash))
    `,
    [userId, email, fullName, passwordHash],
  )
}

const [summary] = await connection.execute(`
  SELECT
    COUNT(*) AS total_users,
    SUM(CASE WHEN email IS NULL OR email = '' THEN 1 ELSE 0 END) AS missing_email,
    SUM(CASE WHEN password_hash IS NULL OR password_hash = '' THEN 1 ELSE 0 END) AS missing_password
  FROM users
`)

const [sample] = await connection.execute(`
  SELECT user_id, email, full_name
  FROM users
  ORDER BY created_at DESC, user_id DESC
  LIMIT 8
`)

await connection.end()

console.log(JSON.stringify({ defaultPassword: DEFAULT_PASSWORD, summary, sample }, null, 2))
