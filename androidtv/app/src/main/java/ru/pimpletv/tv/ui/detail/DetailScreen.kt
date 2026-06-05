package ru.pimpletv.tv.ui.detail

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import coil.compose.AsyncImage
import androidx.tv.material3.Button
import androidx.tv.material3.ExperimentalTvMaterial3Api
import androidx.tv.material3.Icon
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Text
import ru.pimpletv.tv.data.MatchSummary
import ru.pimpletv.tv.ui.browse.LiveBadge
import ru.pimpletv.tv.ui.isLive
import ru.pimpletv.tv.ui.kickoffTime
import ru.pimpletv.tv.ui.theme.ScreenPaddingH
import ru.pimpletv.tv.ui.theme.TextSecondary

@OptIn(ExperimentalTvMaterial3Api::class)
@Composable
fun DetailScreen(match: MatchSummary, onWatch: () -> Unit) {
    val focus = remember { FocusRequester() }
    LaunchedEffect(match.id) { runCatching { focus.requestFocus() } }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = ScreenPaddingH, vertical = 48.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            match.tournament?.let {
                Text(it, style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.secondary)
            }
            if (match.isLive()) LiveBadge()
        }

        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(24.dp)) {
            Logo(match.home.logo)
            Text(
                match.home.name,
                style = MaterialTheme.typography.displayLarge,
                color = MaterialTheme.colorScheme.onBackground,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Text("–", style = MaterialTheme.typography.displayMedium, color = TextSecondary)
            Text(
                match.away.name,
                style = MaterialTheme.typography.displayLarge,
                color = MaterialTheme.colorScheme.onBackground,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Logo(match.away.logo)
        }

        InfoLine("Kickoff", match.kickoffTime())
        match.channel?.let { InfoLine("Channel", it) }

        if (match.isLive()) {
            Button(onClick = onWatch, modifier = Modifier.focusRequester(focus)) {
                Icon(Icons.Filled.PlayArrow, contentDescription = null)
                Text("  Watch on Ace Stream", style = MaterialTheme.typography.titleMedium)
            }
        } else {
            Text(
                "Stream links appear about an hour before kickoff.",
                style = MaterialTheme.typography.titleMedium,
                color = TextSecondary,
                modifier = Modifier.focusRequester(focus),
            )
        }
    }
}

@Composable
private fun InfoLine(label: String, value: String) {
    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("$label:", style = MaterialTheme.typography.titleMedium, color = TextSecondary)
        Text(value, style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.onBackground)
    }
}

@Composable
private fun Logo(url: String?) {
    AsyncImage(
        model = url,
        contentDescription = null,
        contentScale = ContentScale.Fit,
        modifier = Modifier.size(72.dp).clip(CircleShape),
    )
}
