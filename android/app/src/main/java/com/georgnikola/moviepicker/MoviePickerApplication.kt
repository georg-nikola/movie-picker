package com.georgnikola.moviepicker

import android.app.Application
import com.georgnikola.moviepicker.data.MoviesRepository

class MoviePickerApplication : Application() {
    val repository: MoviesRepository by lazy {
        MoviesRepository(applicationContext)
    }
}
