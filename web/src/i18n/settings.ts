export const fallbackLng = 'en-US'
export const languages = ['en-US', 'es', 'pt-BR', 'zh-CN', 'ja'] as const
export type Language = (typeof languages)[number]

export const languageNames: Record<Language, string> = {
  'en-US': 'English',
  'es': 'Español',
  'pt-BR': 'Português',
  'zh-CN': '简体中文',
  'ja': '日本語',
}

export const defaultNS = 'common'
export const cookieName = 'NEXT_LOCALE'

export function getOptions(lng = fallbackLng, ns: string | string[] = defaultNS) {
  return {
    supportedLngs: languages,
    fallbackLng,
    lng,
    fallbackNS: defaultNS,
    defaultNS,
    ns,
  }
}
