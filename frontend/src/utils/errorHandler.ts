/**
 * 错误处理工具
 * 将后端错误转换为用户友好的提示信息
 */

export interface ErrorInfo {
  title: string
  message: string
  type: 'error' | 'warning' | 'info'
}

/**
 * 解析错误并返回友好的提示信息
 */
export function parseError(error: any): ErrorInfo {
  // 网络连接错误
  if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
    return {
      title: '网络连接失败',
      message: '无法连接到服务器，请检查网络连接或服务是否启动',
      type: 'error'
    }
  }

  // TTS 服务不可用
  if (error.response?.status === 503 || 
      error.message?.includes('TTS') || 
      error.message?.includes('GPT-SoVITS')) {
    return {
      title: 'TTS 服务不可用',
      message: '语音合成服务未启动，对话功能正常，但无法生成语音',
      type: 'warning'
    }
  }

  // 超时错误
  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    return {
      title: '请求超时',
      message: '服务响应时间过长，请稍后重试',
      type: 'warning'
    }
  }

  // 服务器错误
  if (error.response?.status >= 500) {
    return {
      title: '服务器错误',
      message: '服务器处理请求时出错，请稍后重试',
      type: 'error'
    }
  }

  // 请求错误（400系列）
  if (error.response?.status >= 400 && error.response?.status < 500) {
    const msg = error.response?.data?.msg || error.response?.data?.message
    return {
      title: '请求失败',
      message: msg || '请求参数有误，请检查后重试',
      type: 'error'
    }
  }

  // 其他未知错误
  return {
    title: '操作失败',
    message: '发生未知错误，请重试',
    type: 'error'
  }
}

/**
 * 简化错误信息，避免暴露技术细节
 */
export function sanitizeErrorMessage(message: string): string {
  // 移除接口路径
  message = message.replace(/\/api\/[^\s]+/g, '接口')
  
  // 移除端口号
  message = message.replace(/:\d{4,5}/g, '')
  
  // 移除 localhost 等技术细节
  message = message.replace(/localhost|127\.0\.0\.1/g, '服务器')
  
  // 限制长度
  if (message.length > 100) {
    message = message.substring(0, 100) + '...'
  }
  
  return message
}
