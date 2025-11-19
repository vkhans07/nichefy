import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Nichefy - Discover Niche Artists',
  description: 'Find niche artists similar to your favorite popular musicians',
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

