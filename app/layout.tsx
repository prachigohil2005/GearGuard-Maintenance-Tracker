import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'GearGuard maintenance tracker',
  description: 'Generated with BLACKBOX AI Builder',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
