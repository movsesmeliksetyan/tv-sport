package ru.pimpletv.tv.ui.browse

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import androidx.tv.material3.Card
import androidx.tv.material3.CardDefaults
import androidx.tv.material3.ExperimentalTvMaterial3Api
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Text
import ru.pimpletv.tv.data.MatchSummary
import ru.pimpletv.tv.ui.isLive
import ru.pimpletv.tv.ui.kickoffTime
import ru.pimpletv.tv.ui.theme.SurfaceVariant
import ru.pimpletv.tv.ui.theme.TextSecondary

private val CardWidth = 260.dp

@OptIn(ExperimentalTvMaterial3Api::class)
@Composable
fun MatchCard(match: MatchSummary, onClick: () -> Unit, modifier: Modifier = Modifier) {
    Card(
        onClick = onClick,
        modifier = modifier.width(CardWidth),
        shape = CardDefaults.shape(RoundedCornerShape(14.dp)),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = match.kickoffTime(),
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.secondary,
                )
                if (match.isLive()) {
                    Box(Modifier.width(10.dp))
                    LiveBadge()
                }
            }
            Box(Modifier.size(0.dp, 12.dp))
            TeamRow(name = match.home.name, logo = match.home.logo)
            Box(Modifier.size(0.dp, 8.dp))
            TeamRow(name = match.away.name, logo = match.away.logo)
            Box(Modifier.size(0.dp, 12.dp))
            Text(
                text = match.tournament ?: (match.channel ?: ""),
                style = MaterialTheme.typography.bodyMedium,
                color = TextSecondary,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
private fun TeamRow(name: String, logo: String?) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        AsyncImage(
            model = logo,
            contentDescription = null,
            contentScale = ContentScale.Fit,
            modifier = Modifier
                .size(32.dp)
                .clip(CircleShape),
        )
        Text(
            text = name,
            style = MaterialTheme.typography.titleLarge,
            color = MaterialTheme.colorScheme.onSurface,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
    }
}
