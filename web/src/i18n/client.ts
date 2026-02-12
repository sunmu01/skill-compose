'use client'

import i18next from 'i18next'
import { initReactI18next, useTranslation as useTranslationOrg } from 'react-i18next'
import resourcesToBackend from 'i18next-resources-to-backend'
import { getOptions, languages, fallbackLng, Language, cookieName } from './settings'

// Initialize i18next for client-side
const runsOnServerSide = typeof window === 'undefined'

// Get language from cookie
function getLanguageFromCookie(): Language {
  if (runsOnServerSide) return fallbackLng

  const match = document.cookie.match(new RegExp(`(^| )${cookieName}=([^;]+)`))
  const lang = match ? match[2] : null

  if (lang && languages.includes(lang as Language)) {
    return lang as Language
  }
  return fallbackLng
}

// Set language cookie
export function setLanguageCookie(lang: Language) {
  document.cookie = `${cookieName}=${lang};path=/;max-age=31536000` // 1 year
}

// Initialize i18next once
let initialized = false

export function initI18next(lng?: Language) {
  const language = lng || getLanguageFromCookie()

  if (!initialized) {
    i18next
      .use(initReactI18next)
      .use(
        resourcesToBackend(
          (language: string, namespace: string) =>
            import(`./locales/${language}/${namespace}.json`)
        )
      )
      .init({
        ...getOptions(language),
        lng: language,
        detection: {
          order: ['cookie'],
          caches: ['cookie'],
        },
        preload: runsOnServerSide ? languages : [],
      })
    initialized = true
  } else if (i18next.language !== language) {
    i18next.changeLanguage(language)
  }

  return i18next
}

// Export useTranslation hook
export function useTranslation(ns?: string | string[], options?: { keyPrefix?: string }) {
  const i18n = initI18next()
  return useTranslationOrg(ns, { i18n, ...options })
}

// Export changeLanguage function
export function changeLanguage(lng: Language) {
  setLanguageCookie(lng)
  // Reload to apply new language — i18next re-initializes from cookie on load
  window.location.reload()
}

// Export current language getter
export function getCurrentLanguage(): Language {
  if (runsOnServerSide) return fallbackLng
  return (i18next.language as Language) || getLanguageFromCookie()
}
