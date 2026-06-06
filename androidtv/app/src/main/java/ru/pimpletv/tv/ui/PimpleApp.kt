package ru.pimpletv.tv.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.repeatOnLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import ru.pimpletv.tv.acestream.AceStream
import ru.pimpletv.tv.data.MatchSummary
import ru.pimpletv.tv.data.Stream
import ru.pimpletv.tv.ui.browse.BrowseScreen
import ru.pimpletv.tv.ui.theme.Background
import ru.pimpletv.tv.ui.theme.PimpleTvTheme

private const val POLL_INTERVAL_MS = 60_000L  // refresh list + stream availability every 60s

private data class Message(val title: String, val body: String)

private val NOT_INSTALLED = Message(
    "Ace Stream not found",
    "Install Ace Stream Media Center (TV build) on this device, then try again. " +
        "It is sideloaded from acestream.org — it is not on Google Play.",
)
private val NO_LINK_YET = Message(
    "No stream yet",
    "Stream links appear about an hour before kickoff. Check back closer to game time.",
)

/**
 * Root composable. No detail page — selecting a match with a link launches Ace
 * Stream directly (a quick chooser appears only when there are several streams).
 */
@Composable
fun PimpleApp(viewModel: MatchViewModel = viewModel()) {
    PimpleTvTheme {
        val state by viewModel.state.collectAsStateWithLifecycle()
        val context = LocalContext.current
        val scope = rememberCoroutineScope()

        var chooser by remember { mutableStateOf<List<Stream>?>(null) }
        var message by remember { mutableStateOf<Message?>(null) }

        // Lifecycle-aware polling: refresh on resume, then every POLL_INTERVAL_MS while
        // foregrounded; repeatOnLifecycle cancels the loop when the app is backgrounded (T3.5).
        val lifecycleOwner = LocalLifecycleOwner.current
        LaunchedEffect(Unit) {
            lifecycleOwner.repeatOnLifecycle(Lifecycle.State.RESUMED) {
                while (true) {
                    viewModel.poll()
                    delay(POLL_INTERVAL_MS)
                }
            }
        }

        fun play(stream: Stream) {
            chooser = null
            if (!AceStream.launch(context, stream.contentId)) message = NOT_INSTALLED
        }

        fun onSelect(match: MatchSummary) {
            if (!match.isLive()) { message = NO_LINK_YET; return }
            if (!AceStream.isInstalled(context)) { message = NOT_INSTALLED; return }
            scope.launch {
                val streams = viewModel.streamsFor(match.id)
                when {
                    streams.isEmpty() -> message = NO_LINK_YET
                    streams.size == 1 -> play(streams.first())
                    else -> chooser = streams
                }
            }
        }

        Box(Modifier.fillMaxSize().background(Background)) {
            BrowseScreen(state = state, onMatchClick = ::onSelect, onRetry = viewModel::refresh)

            chooser?.let { streams ->
                StreamChooser(streams = streams, onPick = ::play, onDismiss = { chooser = null })
            }
            message?.let { msg ->
                MessageDialog(title = msg.title, body = msg.body, onDismiss = { message = null })
            }
        }
    }
}
