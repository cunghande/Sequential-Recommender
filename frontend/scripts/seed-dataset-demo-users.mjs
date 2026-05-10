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

const users = []
for (let id = 1; id <= 20; id += 1) {
  users.push([String(id), `dataset${id}@demo.local`, `Dataset User ${id}`, passwordHash])
}
users.push(["demo", "demo@example.com", "Demo User", passwordHash])

for (const user of users) {
  await connection.execute(
    `
    INSERT INTO users (user_id, email, full_name, password_hash)
    VALUES (?, ?, ?, ?)
    ON DUPLICATE KEY UPDATE
      email = VALUES(email),
      full_name = VALUES(full_name),
      password_hash = VALUES(password_hash)
    `,
    user,
  )
}

const [sample] = await connection.execute(`
  SELECT user_id, email, full_name
  FROM users
  WHERE user_id IN ('1','2','3','4','5','demo')
  ORDER BY FIELD(user_id, 'demo','1','2','3','4','5')
`)

await connection.end()
console.log(JSON.stringify({ defaultPassword: DEFAULT_PASSWORD, sample }, null, 2))
