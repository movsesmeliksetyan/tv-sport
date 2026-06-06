package ru.pimpletv.tv.ui.browse

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.ExperimentalTvMaterial3Api
import androidx.tv.material3.Icon
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import ru.pimpletv.tv.data.MatchSummary
import ru.pimpletv.tv.ui.isLive
import ru.pimpletv.tv.ui.kickoffTime
import ru.pimpletv.tv.ui.theme.Accent
import ru.pimpletv.tv.ui.theme.Background
import ru.pimpletv.tv.ui.theme.SurfaceVariant
import ru.pimpletv.tv.ui.theme.TextSecondary

/**
 * Large featured banner for the top match (modern TV hero pattern). The whole
 * banner is a focusable, clickable Surface so the D-pad can always return to it
 * (a non-live hero has no inner button, which previously made it unreachable).
 */
@OptIn(ExperimentalTvMaterial3Api::class)
@Composable
fun FeaturedHero(match: MatchSummary, onClick: () -> Unit, modifier: Modifier = Modifier) {
    Surface(
        onClick = onClick,
        modifier = modifier.fillMaxWidth().height(300.dp),
        shape = ClickableSurfaceDefaults.shape(RoundedCornerShape(20.dp)),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = SurfaceVariant,
            focusedContainerColor = SurfaceVariant,
        ),
    ) {
        Box(
            Modifier
                .fillMaxSize()
                .background(Brush.horizontalGradient(listOf(SurfaceVariant, Background)))
                .padding(36.dp),
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = if (match.isLive()) "LIVE NOW" else "FEATURED",
                        style = MaterialTheme.typography.labelLarge,
                        color = if (match.isLive()) MaterialTheme.colorScheme.primary else Accent,
                        fontWeight = FontWeight.Bold,
                    )
                    match.tournament?.let {
                        Text(
                            text = "   •   $it",
                            style = MaterialTheme.typography.titleMedium,
                            color = TextSecondary,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                }

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(18.dp),
                ) {
                    HeroLogo(match.home.logo)
                    Text(
                        text = match.home.name,
                        style = MaterialTheme.typography.displayMedium,
                        color = MaterialTheme.colorScheme.onSurface,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text("vs", style = MaterialTheme.typography.headlineMedium, color = TextSecondary)
                    Text(
                        text = match.away.name,
                        style = MaterialTheme.typography.displayMedium,
                        color = MaterialTheme.colorScheme.onSurface,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    HeroLogo(match.away.logo)
                }

                Text(
                    text = buildString {
                        append("Kickoff ").append(match.kickoffTime())
                        match.channel?.let { append("   ·   ").append(it) }
                    },
                    style = MaterialTheme.typography.bodyLarge,
                    color = TextSecondary,
                )

                // Status line (visual only — the whole Surface is the click target).
                Row(verticalAlignment = Alignment.CenterVertically) {
                    if (match.isLive()) {
                        Icon(
                            Icons.Filled.PlayArrow,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary,
                        )
                        Text(
                            "  Watch",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.primary,
                            fontWeight = FontWeight.Bold,
                        )
                    } else {
                        Text(
                            "⏳  Stream links appear about an hour before kickoff",
                            style = MaterialTheme.typography.titleMedium,
                            color = Accent,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun HeroLogo(url: String?) {
    AsyncImage(
        model = url,
        contentDescription = null,
        contentScale = ContentScale.Fit,
        modifier = Modifier
            .size(64.dp)
            .clip(CircleShape),
    )
}
