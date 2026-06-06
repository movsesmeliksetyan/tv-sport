package ru.pimpletv.tv.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import ru.pimpletv.tv.data.MatchRepository
import ru.pimpletv.tv.data.MatchSummary
import ru.pimpletv.tv.data.Stream

sealed interface BrowseUiState {
    data object Loading : BrowseUiState
    data class Error(val message: String) : BrowseUiState
    data class DaySection(val label: String, val matches: List<MatchSummary>)
    data class Content(
        val live: List<MatchSummary>,
        val days: List<DaySection>,
        val featured: List<MatchSummary>,
    ) : BrowseUiState
}

class MatchViewModel(
    private val repository: MatchRepository = MatchRepository(),
) : ViewModel() {

    private val _state = MutableStateFlow<BrowseUiState>(BrowseUiState.Loading)
    val state: StateFlow<BrowseUiState> = _state.asStateFlow()

    /** Fetch resolved streams for a match (detail endpoint) just before launching. */
    suspend fun streamsFor(id: String): List<Stream> =
        runCatching { repository.match(id).streams }.getOrDefault(emptyList())

    /** Manual/full refresh — shows the loading state (e.g. retry from the error screen). */
    fun refresh() {
        _state.value = BrowseUiState.Loading
        fetch()
    }

    /** Silent poll — refreshes data without blanking the screen; keeps last good data on error. */
    fun poll() = fetch()

    private fun fetch() {
        viewModelScope.launch {
            runCatching { repository.matches() }
                .onSuccess { response -> _state.value = toContent(response.matches) }
                .onFailure { e ->
                    // Don't replace good content with an error during background polling.
                    if (_state.value !is BrowseUiState.Content) {
                        _state.value = BrowseUiState.Error(e.message ?: "Unknown error")
                    }
                }
        }
    }

    private fun toContent(all: List<MatchSummary>): BrowseUiState.Content {
        val today = today()
        val days = all
            .filter { it.kickoffDate() != null }
            .groupBy { it.kickoffDate()!! }
            .toSortedMap()
            .map { (date, list) ->
                BrowseUiState.DaySection(
                    label = dayLabel(date, today),
                    matches = list.sortedBy { it.kickoff },
                )
            }
        val live = all.filter { it.isLive() }
        return BrowseUiState.Content(
            live = live,
            days = days,
            featured = (live.ifEmpty { all }).take(6),
        )
    }
}
