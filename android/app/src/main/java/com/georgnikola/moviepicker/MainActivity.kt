package com.georgnikola.moviepicker

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.georgnikola.moviepicker.ui.home.HomeScreen
import com.georgnikola.moviepicker.ui.theme.MoviePickerTheme
import com.georgnikola.moviepicker.ui.watched.WatchedScreen

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MoviePickerTheme {
                MoviePickerApp()
            }
        }
    }
}

@Composable
fun MoviePickerApp() {
    val navController = rememberNavController()
    NavHost(navController = navController, startDestination = "home") {
        composable("home") {
            HomeScreen(onNavigateToWatched = { navController.navigate("watched") })
        }
        composable("watched") {
            WatchedScreen(onBack = { navController.popBackStack() })
        }
    }
}
