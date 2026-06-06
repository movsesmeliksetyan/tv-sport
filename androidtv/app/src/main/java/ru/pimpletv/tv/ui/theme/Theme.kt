package ru.pimpletv.tv.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.darkColorScheme

// Sporty, high-contrast dark palette for 10-foot viewing.
val Background = Color(0xFF0A0E0F)
val Surface = Color(0xFF14191B)
val SurfaceVariant = Color(0xFF1E2629)
val Primary = Color(0xFF00E676)      // vivid pitch-green
val OnPrimary = Color(0xFF00210E)
val Accent = Color(0xFFFFC400)       // amber highlight
val LiveRed = Color(0xFFFF5252)
val TextPrimary = Color(0xFFF5F7F8)
val TextSecondary = Color(0xFF9FB0B5)

// Overscan-safe screen margins (TV safe area).
val ScreenPaddingH = 48.dp
val ScreenPaddingV = 24.dp

private val PimpleColorScheme = darkColorScheme(
    primary = Primary,
    onPrimary = OnPrimary,
    secondary = Accent,
    onSecondary = Color(0xFF221B00),
    background = Background,
    onBackground = TextPrimary,
    surface = Surface,
    onSurface = TextPrimary,
    surfaceVariant = SurfaceVariant,
    onSurfaceVariant = TextSecondary,
    border = Color(0xFF2C383C),
)

@Composable
fun PimpleTvTheme(content: @Composable () -> Unit) {
    @Suppress("UNUSED_EXPRESSION") isSystemInDarkTheme() // TV is always dark; kept for clarity
    MaterialTheme(
        colorScheme = PimpleColorScheme,
        typography = PimpleTypography,
        content = content,
    )
}
