package com.georgnikola.moviepicker.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.georgnikola.moviepicker.data.MoviesRepository
import com.georgnikola.moviepicker.data.PickedMovie
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class HomeUiState(
    val currentPick: PickedMovie? = null,
    val history: List<PickedMovie> = emptyList(),
    val watchedMovies: Set<String> = emptySet(),
    val skipWatched: Boolean = false,
) {
    val watchedCount: Int get() = watchedMovies.size
    val currentIsWatched: Boolean get() = currentPick?.title in watchedMovies
}

class HomeViewModel(private val repository: MoviesRepository) : ViewModel() {

    private val _uiState = MutableStateFlow(HomeUiState())
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            combine(repository.watchedMovies, repository.skipWatched) { watched, skip ->
                Pair(watched, skip)
            }.collect { (watched, skip) ->
                _uiState.update { it.copy(watchedMovies = watched, skipWatched = skip) }
            }
        }
    }

    fun pickMovie() {
        val state = _uiState.value
        val pick = repository.pickRandom(state.watchedMovies, state.skipWatched)
        _uiState.update { current ->
            current.copy(
                currentPick = pick,
                history = (listOf(pick) + current.history).take(50)
            )
        }
    }

    fun toggleWatched(title: String) {
        viewModelScope.launch {
            if (title in _uiState.value.watchedMovies) {
                repository.removeWatched(title)
            } else {
                repository.addWatched(title)
            }
        }
    }

    fun setSkipWatched(skip: Boolean) {
        viewModelScope.launch { repository.setSkipWatched(skip) }
    }
}

class HomeViewModelFactory(private val repository: MoviesRepository) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T = HomeViewModel(repository) as T
}
