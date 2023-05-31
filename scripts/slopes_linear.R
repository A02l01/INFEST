library(ggplot2)
library(ggrepel)
library(segmented)
library(cowplot)

range_regex <- function(str) {
  re <- regexpr(
    "(?P<min>[[:digit:]]+)[-,:](?P<max>[[:digit:]]+)",
    str,
    perl = TRUE,
    ignore.case = TRUE
  )
  return(re)
}


extract_re_matches <- function(str, re) {
  if (re == 0) {
    stop("Cannot extract from non-match")
  }

  starts <- as.integer(unname(attr(re, "capture.start")[1, ]))
  lengths <- as.integer(unname(attr(re, "capture.length")[1, ]))
  n <- attr(re, "capture.names")

  s <- substring(str, starts, (starts + (lengths - 1)))
  li <- list()

  for (i in seq_along(n)) {
    name <- n[i]
    str <- s[i]
    li[name] <- as.character(str)
  }

  return(li)
}


get_minmax <- function() {
  answer_map <- c("s" = "s", "skip" = "s")

  success <- FALSE
  minmax <- NA
  while (!success) {
    minmax <- trimws(tolower(readline(
      "Enter limit [int,int]=range, [s]=skip > "
    )))
    minmax <- gsub("[[:space:]]+", "", minmax, perl = TRUE)

    r <- range_regex(minmax)

    if (minmax == "") {
      print("Please enter a range or s to skip.")
    } else if (minmax %in% names(answer_map)) {
      minmax <- unname(answer_map[minmax])
      success <- TRUE
    } else if (r) {
      minmax <- extract_re_matches(minmax, r)
      minmax <- lapply(minmax, FUN = as.integer)
      if (minmax$min >= minmax$max) {
        print(sprintf(
          "Your minimum value %d was greater than your maximum value %d.",
          minmax$min,
          minmax$max
        ))
        print("Please try again")
        success <- FALSE
      } else {
        success <- TRUE
      }
    } else {
      print("Sorry, you entered an unsupported option.")
    }
  }
  return(minmax)
}


get_check_ok <- function() {
  answer <- "NA"
  answer_map <- c(
    "o" = "o", "y" = "o", "oui" = "o",
    "n" = "n", "non" = "n", "no" = "n",
    "r" = "r", "redo" = "r", "refaire" = "r"
  )

  while (!answer %in% names(answer_map)) {
    answer <- trimws(tolower(readline(
      "Is it ok? [[o]=[y]=oui=yes, [n]=non=no, [r]=redo=refaire > "
    )))

    if (!answer %in% names(answer_map)) {
      print(sprintf("Invalid option specified: '%s'", answer))
    }
  }
  return(answer)
}


#' Approximation of derivative.
forward_difference <- function(arr, order = 1) {
  n <- length(arr)
  f <- arr[(1 + order):n] - arr[1:(n - order)]
  # Pad left with zeros
  f <- c(numeric(order), f)
  return(f)
}


#' Approximation of second derivative.
forward_difference2 <- function(arr, order = 1) {
  one <- forward_difference(arr, order = order)
  two <- forward_difference(one, order = order)
  return(two)
}


plotit <- function(
  sdf,
  sample = NULL,
  midpoint = NULL,
  min_lines = 200,
  bandwidth = 10,
  order = 10,
  normalize = FALSE
) {
  # Make sure we're not mutating sdf
  sdf <- data.frame(sdf)
  if (normalize && ("leaf_area" %in% names(sdf))) {
    sdf[["lesion_area"]] <- sdf[["lesion_area"]] / sdf[["leaf_area"]]
  }
  y <- sdf[["lesion_area"]]
  k <- ksmooth(
    sdf[["time"]],
    sdf[["lesion_area"]] / max(sdf[["lesion_area"]], na.rm = TRUE),
    kernel = "normal",
    bandwidth = bandwidth
  )

  ysm <- k$y
  d1 <- forward_difference(ysm, order = order)
  d2 <- forward_difference2(ysm, order = order)

  zeros2 <- which(overlaps_zero(d2, direction = "reverse") & (abs(d1) > 1e-3))
  maxima <- find_local_maxima(d2, tolerance = 2e-5, min_block = 12)
  maxima2 <- find_local_maxima(
    d2,
    tolerance = -2e-5,
    min_block = 12,
    minima = TRUE
  )

  max_raw <- which.max(y)
  max_smoothed <- which.max(ysm)
  max_ <- max(c(max_raw, max_smoothed, min_lines))
  zeros2 <- zeros2[zeros2 <= max_]
  maxima <- maxima[maxima <= max_]
  maxima2 <- maxima2[maxima2 <= max_]

  p <- ggplot() +
    geom_point(data = sdf, aes(x = time, y = lesion_area), alpha = 0.3) +
    geom_line(aes(x = sdf$time, y = sdf$lesion_smoothed), color = "black") +
    theme_bw() +
    geom_vline(xintercept = maxima, color = "blue") +
    geom_text_repel(
      aes(x = maxima, y = 0.85 * max(y), label = maxima),
      min.segment.length = 1
    ) +
    geom_vline(xintercept = zeros2, color = "red") +
    geom_text_repel(
      aes(x = zeros2, y = 0.9 * max(y), label = zeros2),
      min.segment.length = 1
    ) +
    geom_vline(xintercept = maxima2, color = "green") +
    geom_text_repel(
      aes(x = maxima2, y = 0.95 * max(y), label = maxima2),
      min.segment.length = 1
    ) +
    scale_x_continuous(
      breaks = better_breaks_maj,
      minor_breaks = better_breaks_min
    )

  if (!is.null(midpoint) & (length(midpoint) > 0)) {
    p <- p + geom_vline(xintercept = midpoint, color = "orange") +
      geom_text_repel(
        aes(
          x = midpoint,
          y = 0.70 * max(sdf$y, na.rm = TRUE),
          label = midpoint
        ),
        min.segment.length = 1
      )
  }

  if (!is.null(sample)) {
    p <- p + ggtitle(sample)
  }

  if (normalize && ("leaf_area" %in% names(sdf))) {
    p <- p + ylab("lesion_area / leaf_area")
  }
  return(p)
}


split_with_overlap <- function(vec, size, step = 1) {
  starts <- seq(1, length(vec) - size, by = step)
  ends <- starts + size - 1
  ends[ends > length(vec)] <- length(vec)

  li <- lapply(seq_along(starts), function(i) vec[starts[i]:ends[i]])
  return(li)
}


find_local_maxima <- function(
  arr,
  tolerance = 1e-5,
  min_block = 5,
  minima = FALSE
) {
  fwd_filter <- c(FALSE, rep(TRUE, min_block))

  if (minima) {
    arr_thresholded <- arr < tolerance
  } else {
    arr_thresholded <- arr > tolerance
  }
  arr_split <- split_with_overlap(arr_thresholded, size = min_block + 1)
  rev_arr_split <- split_with_overlap(
    rev(arr_thresholded),
    size = min_block + 1
  )
  fwd <- which(vapply(
    arr_split,
    FUN.VALUE = TRUE,
    FUN = function(li) all(li == fwd_filter)
  ))
  rev_ <- which(rev(vapply(
    rev_arr_split,
    FUN.VALUE = TRUE,
    FUN = function(li) all(li == fwd_filter)
  )))
  len <- min(c(length(fwd), length(rev_)))
  if (len < 1) {
    return(numeric(0))
  }
  coords <- matrix(c(fwd[1:len], rev_[1:len]), ncol = 2, nrow = len)

  if (minima) {
    maxima <- apply(
      coords,
      MARGIN = 1,
      FUN = function(x) x[1] + which.min(arr[x[1]:x[2]])
    )
  } else {
    maxima <- apply(
      coords,
      MARGIN = 1,
      FUN = function(x) x[1] + which.max(arr[x[1]:x[2]])
    )
  }
  return(maxima)
}


overlaps_zero <- function(arr, zero = 0.0, direction = "both") {
  n <- length(arr)

  f1 <- (arr[2:n] > zero) &  (arr[1:(n - 1)] <= zero)
  f2 <- (arr[2:n] < zero) & (arr[1:(n - 1)] >= zero)

  if (direction == "both") {
    f <- f1  | f2
  } else if (direction == "forward") {
    f <- f1
  } else if (direction == "reverse") {
    f <- f2
  } else {
    stop("direction must be both, forward or reverse")
  }
  # Pad left with zeros
  f <- c(FALSE, f)
  return(f)
}


find_initial_slope <- function(df, span, normalize = FALSE) {
  # Make sure we're not mutating sdf
  df <- data.frame(df)
  if (normalize && ("leaf_area" %in% names(df))) {
    df[["lesion_area"]] <- df[["lesion_area"]] / df[["leaf_area"]]
  }

  mm <- max(df[["lesion_area"]]) * 0.5
  mm <- (max(df[["lesion_area"]]) - min(df[["lesion_area"]])) * 0.5
  ts <- df[["time"]][which.max(abs(df[["lesion_area"]]))]
  ssd <- subset(df, subset = (df[["time"]] < ts))
  max_ <- ssd$time[which.min(abs(ssd[["lesion_area"]] - mm))]
  mfit <- ksmooth(
    df[["time"]],
    df[["lesion_area"]],
    kernel = "normal",
    bandwidth = span
  )
  return(list(
    "mm" = mm,
    "ts" = ts,
    "ssd" = ssd,
    "max" = max_,
    "mfit" = mfit
  ))
}


better_breaks <- function(start, end, everyn = 1) {
  multiples <- floor(log10(end))

  threshold1 <- (10 ** multiples) * 2.5
  threshold2 <- (10 ** multiples) * 5
  if (end < threshold1) {
    stepsize <- (10 ** (multiples - 1))
  } else if (end < threshold2) {
    stepsize <- (10 ** (multiples - 1)) * 2.5
  } else {
    stepsize <- (10 ** (multiples - 1)) * 5
  }

  breaks <- seq(0, end, stepsize * (everyn / 2))
  return(breaks)
}


better_breaks_maj <- function(lims, n = 4) {
  end <- lims[2]
  return(better_breaks(0, end, n))
}


better_breaks_min <- function(lims, n = 1) {
  end <- lims[2]
  return(better_breaks(0, end, n))
}


#' Interactively find the slope for nauvitron sample.
#'
#' @param d The dataframe of time-series measurements from the nauvitron.
#'   This should have the columns id, time, lesion_area
#' @param myfile The path where the results should be stored.
#'   If this file exists, it will be read and any previously curated samples
#'   will be skipped.
#' @param span The bandwidth of the kernel used to create a smoothed line.
#'   This affects the smoothed line used in plotting, and the guide bars showing
#'   inflection points. It is usually best to keep this >20 and <100 assuming a
#'   10 minute sampling interval.
#' @param plot_normalized If your dataframe has the leaf area, the screen
#'   where you select the ranges will also have the lesion size / leaf size
#'   plot. This is often a bit smoother, and can make boundary decisions easier.
#'
#' @returns
compute_slope <- function(df, myfile, span = 60, plot_normalized = TRUE) {

  if (!all(names(df)[1:3] == c("id", "time", "lesion_area"))) {
    stop(paste0(
      "The dataframe needs to have the columns ",
      "id, time, lesion_area to work properly."
    ))
  }

  plot_leaf_area <- ("leaf_area" %in% names(df)) & plot_normalized

  samples <- unique(df$id)
  nsamples <- length(samples)

  if (file.exists(myfile)) {
    deja <- read.table(
      myfile,
      sep = "\t",
      header = FALSE,
      col.names = c(
        "id", "slope", "decision", "range_start", "psi", "range_end"
      )
    )
    samples <- setdiff(samples, deja[["id"]])
    i <- nsamples - length(samples) + 1
    rm(deja)
  } else {
    i <- 1
  }

  while (i <= length(samples)) {
    uy <- samples[i]

    print(sprintf("Processing samples %s: %d of %d", uy, i, nsamples))
    sdf <- subset(df, subset = (df$id == uy))

    init_slope <- find_initial_slope(sdf, span)

    sdf$lesion_smoothed <- init_slope$mfit$y
    suppressWarnings(suppressMessages(
      p <- plotit(sdf, midpoint = init_slope$max, sample = uy, bandwidth = span)
    ))

    if (plot_leaf_area) {

      init_slope2 <- find_initial_slope(sdf, span, normalize = TRUE)

      sdf$lesion_smoothed <- init_slope2$mfit$y
      suppressWarnings(suppressMessages({
        p2 <- plotit(
          sdf,
          midpoint = init_slope2$max,
          bandwidth = span,
          normalize = TRUE
        )
        p <- plot_grid(p, p2, nrow = 2, ncol = 1, align = "hv")
      }))
    }

    print(p)

    # Prompts user for range
    minmax <- get_minmax()

    if (is.list(minmax)) {
      sdf <- subset(
        sdf,
        subset = (
          (sdf$id == uy) &
          (sdf$time > minmax$min) &
          (sdf$time < minmax$max)
        )
      )
      x <- sdf$time
      y <- log(sdf$lesion_area + 1E-9)
      y[which(y == -Inf)] <- NA

      if (is.na(sum(y)) != TRUE) {
        for (jj in 1:1) {
          out_lm <- lm(y ~ x)
          o <- segmented(out_lm, seg.Z = ~ x)
          fit <- numeric(length(x)) * NA
          fit[complete.cases(rowSums(cbind(y, x)))] <- broken.line(o)$fit
          if (jj == 1) {
            val <- sd(o$residuals)
            y[which(o$residuals > val | o$residuals < -val)] <- NA
          }
        }

        data1 <- data.frame(x = x, y = y, fit = fit)
        res <- slope(o)

        breakpoint <- round(o$psi[[2]], 0)
        suppressWarnings(suppressMessages({
          p1 <- ggplot() +
            geom_point(
              data = sdf[sdf$lesion_area > 1, ],
              aes(x = time, y = log(lesion_area + 1E-9)),
              alpha = 0.3
            ) +
            geom_line(data = data1, aes(x = x, y = y), color = "black") +
            geom_line(aes(x = x, y = fit), color = "steelblue") +
            theme_bw() +
            geom_vline(xintercept = o$psi[[2]], color = "red") +
            geom_text_repel(
              aes(
                x = o$psi[[2]],
                y = 0.95 * log(max(sdf[["lesion_area"]], na.rm = TRUE) + 1E-9),
                label = breakpoint
              ),
              min.segment.length = 1
            ) +
            ggtitle(paste(uy, res$x[2, 1], sep = " "))

          p2 <- ggplot() +
            geom_line(data = data1, aes(x = x, y = exp(y)), alpha = 0.3) +
            geom_point(
              data = sdf,
              aes(x = time, y = lesion_area),
              alpha = 0.3
            ) +
            theme_bw() +
            geom_vline(xintercept = o$psi[[2]], color = "red") +
            geom_text_repel(
              aes(
                x = o$psi[[2]],
                y = 0.95 * max(sdf[["lesion_area"]], na.rm = TRUE),
                label = breakpoint
              ),
              min.segment.length = 1
            )
          p <- plot_grid(p1, p2, ncol = 2, nrow = 1, align = "hv")
        }))

        print(p)

        answer <- get_check_ok()

        if (answer != "r") {
          line <- paste(
            uy,
            res$x[2, 1],
            answer,
            minmax$min,
            o$psi[[2]],
            minmax$max,
            sep = "\t"
          )
          write(line, file = myfile, append = TRUE)
          i <- i + 1
        }
      }
    } else if (minmax == "s") {
      line <- paste(uy, NA, "s", NA, NA, NA, sep = "\t")
      i <- i + 1
      write(line, file = myfile, append = TRUE)
    }
  }
}
