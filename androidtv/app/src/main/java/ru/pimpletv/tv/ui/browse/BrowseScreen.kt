package ru.pimpletv.tv.ui.browse

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.tv.material3.ExperimentalTvMaterial3Api
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Text
import ru.pimpletv.tv.data.MatchSummary
import ru.pimpletv.tv.ui.BrowseUiState
import ru.pimpletv.tv.ui.theme.Primary
import ru.pimpletv.tv.ui.theme.ScreenPaddingH
import ru.pimpletv.tv.ui.theme.ScreenPaddingV
import ru.pimpletv.tv.ui.theme.TextSecondary

@OptIn(ExperimentalTvMaterial3Api::class)
@Composable
fun BrowseScreen(
    state: BrowseUiState,
    onMatchClick: (MatchSummary) -> Unit,
    onRetry: () -> Unit,
) {
    when (state) {
        is BrowseUiState.Loading -> CenterMessage("Loading matches…")
        is BrowseUiState.Error -> CenterMessage("Couldn't reach the server.\n${state.message}")
        is BrowseUiState.Content -> Content(state, onMatchClick)
    }
}

@Composable
private fun Content(state: BrowseUiState.Content, onMatchClick: (MatchSummary) -> Unit) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(vertical = ScreenPaddingV),
        verticalArrangement = Arrangement.spacedBy(28.dp),
    ) {
        item {
            Box(Modifier.padding(horizontal = ScreenPaddingH)) {
                Text(
                    text = "PimpleTV",
                    style = MaterialTheme.typography.displayLarge,
                    color = Primary,
                )
            }
        }
        state.featured.firstOrNull()?.let { hero ->
            item {
                Box(Modifier.padding(horizontal = ScreenPaddingH)) {
                    FeaturedHero(hero, onClick = { onMatchClick(hero) })
                }
            }
        }
        matchRow("Live now", state.live, onMatchClick)
        state.days.forEach { day ->
            matchRow(day.label, day.matches, onMatchClick)
        }
    }
}

private fun androidx.compose.foundation.lazy.LazyListScope.matchRow(
    title: String,
    matches: List<MatchSummary>,
    onMatchClick: (MatchSummary) -> Unit,
) {
    if (matches.isEmpty()) return
    item {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(
                text = title,
                style = MaterialTheme.typography.headlineMedium,
                color = MaterialTheme.colorScheme.onBackground,
                modifier = Modifier.padding(horizontal = ScreenPaddingH),
            )
            LazyRow(
                contentPadding = PaddingValues(horizontal = ScreenPaddingH),
                horizontalArrangement = Arrangement.spacedBy(20.dp),
            ) {
                items(matches, key = { it.id }) { match ->
                    MatchCard(match = match, onClick = { onMatchClick(match) })
                }
            }
        }
    }
}

@Composable
private fun CenterMessage(text: String) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text(text, style = MaterialTheme.typography.titleLarge, color = TextSecondary)
    }
}
