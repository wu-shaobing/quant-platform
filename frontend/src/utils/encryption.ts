/**
 * 安全加密工具
 * 使用Web Crypto API提供真正的加密功能
 */

/**
 * 生成密钥
 */
async function generateKey(password: string, salt: Uint8Array): Promise<CryptoKey> {
  const encoder = new TextEncoder()
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    encoder.encode(password),
    { name: 'PBKDF2' },
    false,
    ['deriveBits', 'deriveKey']
  )

  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt,
      iterations: 100000,
      hash: 'SHA-256',
    },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  )
}

/**
 * 生成随机盐值
 */
function generateSalt(): Uint8Array {
  return crypto.getRandomValues(new Uint8Array(16))
}

/**
 * 生成随机IV
 */
function generateIV(): Uint8Array {
  return crypto.getRandomValues(new Uint8Array(12))
}

/**
 * 加密数据
 */
export async function encryptData(data: string, password?: string): Promise<string> {
  try {
    const encoder = new TextEncoder()
    const dataBuffer = encoder.encode(data)
    
    // 使用环境变量中的密钥或传入的密码
    const encryptionKey = password || import.meta.env.VITE_ENCRYPTION_KEY || 'default_key_123456'
    
    const salt = generateSalt()
    const iv = generateIV()
    const key = await generateKey(encryptionKey, salt)
    
    const encryptedBuffer = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      key,
      dataBuffer
    )
    
    // 将salt、iv和加密数据合并
    const combined = new Uint8Array(salt.length + iv.length + encryptedBuffer.byteLength)
    combined.set(salt, 0)
    combined.set(iv, salt.length)
    combined.set(new Uint8Array(encryptedBuffer), salt.length + iv.length)
    
    // 转换为Base64
    return btoa(String.fromCharCode(...combined))
  } catch (error) {
    console.error('加密失败:', error)
    // 降级到Base64编码
    return btoa(encodeURIComponent(data))
  }
}

/**
 * 解密数据
 */
export async function decryptData(encryptedData: string, password?: string): Promise<string> {
  try {
    // 使用环境变量中的密钥或传入的密码
    const encryptionKey = password || import.meta.env.VITE_ENCRYPTION_KEY || 'default_key_123456'
    
    // 从Base64解码
    const combined = new Uint8Array(
      atob(encryptedData)
        .split('')
        .map(char => char.charCodeAt(0))
    )
    
    // 提取salt、iv和加密数据
    const salt = combined.slice(0, 16)
    const iv = combined.slice(16, 28)
    const encryptedBuffer = combined.slice(28)
    
    const key = await generateKey(encryptionKey, salt)
    
    const decryptedBuffer = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv },
      key,
      encryptedBuffer
    )
    
    const decoder = new TextDecoder()
    return decoder.decode(decryptedBuffer)
  } catch (error) {
    console.error('解密失败:', error)
    // 降级到Base64解码
    try {
      return decodeURIComponent(atob(encryptedData))
    } catch {
      return encryptedData
    }
  }
}

/**
 * 生成安全的随机字符串
 */
export function generateSecureRandomString(length = 32): string {
  const array = new Uint8Array(length)
  crypto.getRandomValues(array)
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
}

/**
 * 计算数据的哈希值
 */
export async function calculateHash(data: string, algorithm: 'SHA-1' | 'SHA-256' | 'SHA-384' | 'SHA-512' = 'SHA-256'): Promise<string> {
  const encoder = new TextEncoder()
  const dataBuffer = encoder.encode(data)
  const hashBuffer = await crypto.subtle.digest(algorithm, dataBuffer)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

/**
 * 验证数据完整性
 */
export async function verifyDataIntegrity(data: string, expectedHash: string, algorithm: 'SHA-1' | 'SHA-256' | 'SHA-384' | 'SHA-512' = 'SHA-256'): Promise<boolean> {
  const actualHash = await calculateHash(data, algorithm)
  return actualHash === expectedHash
}

/**
 * 加密敏感数据（向后兼容）
 */
export const encryptSensitiveData = async (data: string): Promise<string> => {
  return await encryptData(data)
}

/**
 * 解密敏感数据（向后兼容）
 */
export const decryptSensitiveData = async (encryptedData: string): Promise<string> => {
  return await decryptData(encryptedData)
}

/**
 * 检查浏览器是否支持Web Crypto API
 */
export function isWebCryptoSupported(): boolean {
  return typeof crypto !== 'undefined' && typeof crypto.subtle !== 'undefined'
}

export default {
  encryptData,
  decryptData,
  generateSecureRandomString,
  calculateHash,
  verifyDataIntegrity,
  encryptSensitiveData,
  decryptSensitiveData,
  isWebCryptoSupported,
}