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

    init { refresh() }

    /** Fetch resolved streams for a match (detail endpoint) just before launching. */
    suspend fun streamsFor(id: String): List<Stream> =
        runCatching { repository.match(id).streams }.getOrDefault(emptyList())

    fun refresh() {
        viewModelScope.launch {
            _state.value = BrowseUiState.Loading
            runCatching { repository.matches() }
                .onSuccess { response ->
                    val all = response.matches
                    val live = all.filter { it.isLive() }
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
                    _state.value = BrowseUiState.Content(
                        live = live,
                        days = days,
                        featured = (live.ifEmpty { all }).take(6),
                    )
                }
                .onFailure { _state.value = BrowseUiState.Error(it.message ?: "Unknown error") }
        }
    }
}
