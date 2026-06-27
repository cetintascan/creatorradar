export async function get(path) {
  const res = await fetch(path)
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
  return res.json()
}
