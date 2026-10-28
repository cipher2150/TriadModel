/** Write tokens live in this browser only. Storage can be unavailable (private mode), so every
 *  access is guarded and the app keeps working without it. */

const key = (id: string): string => `triadmodel.token.${id}`

export function readToken(id: string): string | null {
  try {
    return localStorage.getItem(key(id))
  } catch {
    return null
  }
}

export function storeToken(id: string, token: string): boolean {
  try {
    localStorage.setItem(key(id), token)
    return true
  } catch {
    return false
  }
}

export function forgetToken(id: string): void {
  try {
    localStorage.removeItem(key(id))
  } catch {
    /* nothing to forget */
  }
}

const HASH = /^#\/m\/([0-9a-fA-F-]{36})$/

export const modelIdFromHash = (hash: string): string | null => HASH.exec(hash)?.[1] ?? null

export const hashForModel = (id: string): string => `#/m/${id}`
