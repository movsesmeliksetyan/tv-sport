package ru.pimpletv.tv.ui

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.tv.material3.Button
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import ru.pimpletv.tv.data.Stream
import ru.pimpletv.tv.ui.theme.Surface as SurfaceColor

private val Scrim = Color(0xCC000000)

/** Compact quality/source picker, shown only when a match has >1 stream (FR-6). */
@Composable
fun StreamChooser(streams: List<Stream>, onPick: (Stream) -> Unit, onDismiss: () -> Unit) {
    BackHandler(onBack = onDismiss)
    val first = remember { FocusRequester() }
    LaunchedEffect(Unit) { runCatching { first.requestFocus() } }

    Box(Modifier.fillMaxSize().background(Scrim), contentAlignment = Alignment.Center) {
        Surface(shape = RoundedCornerShape(18.dp), colors = panelColors()) {
            Column(Modifier.padding(28.dp).width(420.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Text("Choose a stream", style = MaterialTheme.typography.headlineMedium,
                    color = MaterialTheme.colorScheme.onSurface)
                streams.forEachIndexed { i, s ->
                    Button(
                        onClick = { onPick(s) },
                        modifier = Modifier.fillMaxWidth().then(if (i == 0) Modifier.focusRequester(first) else Modifier),
                    ) {
                        Text(streamLabel(s), style = MaterialTheme.typography.titleMedium)
                    }
                }
            }
        }
    }
}

/** Generic centered message (no-link-yet, errors, Ace Stream not installed). */
@Composable
fun MessageDialog(title: String, body: String, onDismiss: () -> Unit) {
    BackHandler(onBack = onDismiss)
    val ok = remember { FocusRequester() }
    LaunchedEffect(Unit) { runCatching { ok.requestFocus() } }

    Box(Modifier.fillMaxSize().background(Scrim), contentAlignment = Alignment.Center) {
        Surface(shape = RoundedCornerShape(18.dp), colors = panelColors()) {
            Column(Modifier.padding(28.dp).width(480.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Text(title, style = MaterialTheme.typography.headlineMedium,
                    color = MaterialTheme.colorScheme.onSurface)
                Text(body, style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
                Button(onClick = onDismiss, modifier = Modifier.focusRequester(ok)) {
                    Text("OK", style = MaterialTheme.typography.titleMedium)
                }
            }
        }
    }
}

private fun streamLabel(s: Stream): String {
    val parts = listOfNotNull(s.quality, s.language?.uppercase()).joinToString(" · ")
    return if (parts.isBlank()) "Ace Stream" else parts
}

@Composable
private fun panelColors() = androidx.tv.material3.SurfaceDefaults.colors(
    containerColor = SurfaceColor,
)
