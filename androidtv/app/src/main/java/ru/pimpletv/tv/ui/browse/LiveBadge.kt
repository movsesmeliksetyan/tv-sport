package ru.pimpletv.tv.ui.browse

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Text
import ru.pimpletv.tv.ui.theme.LiveRed

@Composable
fun LiveBadge(modifier: Modifier = Modifier) {
    Text(
        text = "● LIVE",
        style = MaterialTheme.typography.labelLarge,
        color = Color.White,
        modifier = modifier
            .background(LiveRed, RoundedCornerShape(6.dp))
            .padding(horizontal = 8.dp, vertical = 2.dp),
    )
}
