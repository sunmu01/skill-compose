'use client'

import { Globe } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { languages, languageNames, Language } from '@/i18n/settings'
import { changeLanguage, getCurrentLanguage } from '@/i18n/client'
import { useEffect, useState } from 'react'

export function LanguageSwitcher() {
  const [mounted, setMounted] = useState(false)
  const [currentLang, setCurrentLang] = useState<Language>('en-US')

  useEffect(() => {
    setMounted(true)
    setCurrentLang(getCurrentLanguage())
  }, [])

  const handleLanguageChange = (lang: Language) => {
    changeLanguage(lang)
  }

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" className="h-9 w-9">
        <Globe className="h-4 w-4" />
      </Button>
    )
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="h-9 w-9" title={languageNames[currentLang]}>
          <Globe className="h-4 w-4" />
          <span className="sr-only">Select language</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {languages.map((lang) => (
          <DropdownMenuItem
            key={lang}
            onSelect={() => handleLanguageChange(lang)}
            className={currentLang === lang ? 'bg-accent' : ''}
          >
            {languageNames[lang]}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
