package ru.pimpletv.tv.ui

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import ru.pimpletv.tv.data.MatchSummary
import ru.pimpletv.tv.ui.browse.BrowseScreen
import ru.pimpletv.tv.ui.detail.DetailScreen
import ru.pimpletv.tv.ui.theme.Background
import ru.pimpletv.tv.ui.theme.PimpleTvTheme

/** Root composable. Simple state-based navigation: browse <-> detail. */
@Composable
fun PimpleApp(viewModel: MatchViewModel = viewModel()) {
    PimpleTvTheme {
        val state by viewModel.state.collectAsStateWithLifecycle()
        var selected by remember { mutableStateOf<MatchSummary?>(null) }

        Box(Modifier.fillMaxSize().background(Background)) {
            val current = selected
            if (current == null) {
                BrowseScreen(
                    state = state,
                    onMatchClick = { selected = it },
                    onRetry = viewModel::refresh,
                )
            } else {
                BackHandler { selected = null }
                DetailScreen(
                    match = current,
                    onWatch = { /* Phase 4: launch acestream:// */ },
                )
            }
        }
    }
}
