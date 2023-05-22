library("tidyverse")
library("ggrepel")
library("mclust")
library("mcp")
library("segmented")
library("splines")


find_segments <- function(
  response,
  explanatory,
  df = NULL,
  min_segments = 2,
  max_segments = 20,
  min_size = 50,
  plot_it = FALSE
) {
  if (is.null(df)) {
    model <- lm(response ~ explanatory)
    model_segmented = selgmented(
      model,
      seg.Z = ~ explanatory,
      Kmax = max_segments,
      type = "bic",
      th = 0,
      msg = FALSE
    )
  } else {
    e <- df[[explanatory]]
    r <- df[[response]]
    model <- lm(r ~ e)
    model_segmented = selgmented(
      model,
      Kmax = max_segments,
      type = "bic",
      th = 0,
      msg = FALSE
    )
  }

  if (plot_it) {
    plot(model_segmented, res = TRUE)
  }

  psi <- unname(model_segmented$psi[, "Est."])

  if (length(psi) < min_segments) {
    if (min_size <= 1) {
      stop("Couldn't find enough segments in the data. Sorry")
    }
    psi <- find_segments(
      response,
      explanatory,
      df = df,
      min_segments = min_segments,
      max_segments = max_segments,
      min_size = ceiling(min_size / 2),
      plot_it = plot_it
    )
  }

  return(list("psi" = psi, "model" = model_segmented))
}


find_segmented_lines <- function(segments, min_time, max_time, min_segment = 50) {
  su <- summary(segments$model)
  breakpoints <- c(unname(su$psi[, "Initial"]), max_time)
  model_coefs <- slope(segments$model)$e
  slopes <- unname(model_coefs[, "Est."])
  ci_lower <- unname(model_coefs[, "CI(95%).l"])
  ci_upper <- unname(model_coefs[, "CI(95%).u"])

  intercept <- su$coefficients["(Intercept)", "Estimate"]

  df <- data.frame(
    matrix(data = NA, ncol = 11, nrow = length(breakpoints))
  )
  names(df) <- c("id", "x1", "xmid", "x2", "y1", "ymid", "y2", "intercept", "slope", "ci_lower", "ci_upper")

  df[, "x1"] <- c(min_time, breakpoints[1:(length(breakpoints) - 1)])
  df[, "x2"] <- breakpoints
  df[, "xmid"] <- (df[, "x1"] + df[, "x2"]) / 2
  df[, "intercept"] <- intercept
  df[, "slope"] <- slopes
  df[, "ci_lower"] <- ci_lower
  df[, "ci_upper"] <- ci_upper

  for (i in seq_len(nrow(df))) {
    if (i == 1) {
      y1 <- su$coefficients["(Intercept)", "Estimate"]
    } else {
      y1 <- df[i - 1, "y2"]
    }

    intercept <- y1 - (df[i, "x1"] * df[i, "slope"])

    df[i, "y1"] <- y1
    df[i, "y2"] <- intercept + (df[i, "x2"] * df[i, "slope"])
    df[i, "ymid"] <- intercept + (df[i, "xmid"] * df[i, "slope"])

    df[i, "intercept"] <- intercept
  }

  df <- df[abs(df["x1"] - df["x2"]) >= min_segment, ]
  df["id"] <- seq_len(nrow(df))
  return(df)
}


plot_segmented_lines <- function(
  response,
  explanatory,
  segments,
  min_segment = 50,
  df = NULL
) {
  if (!is.null(df)) {
    explanatory <- df[[explanatory]]
    response <- df[[response]]
  }

  sdf <- data.frame(
    explanatory = explanatory,
    response = response
  )

  breakpoints <- segments[2:nrow(segments), "x1"]

  rm(response)
  rm(explanatory)

  gg <- ggplot(sdf, aes(x = explanatory, y = response))
    geom_point(alpha = 0.6, size = 1)
    geom_segment(
      aes(x = x1, y = y1, xend = x2, yend = y2),
      color = "red",
      data = segments,
      linewidth = 1.5,
      alpha = 0.8
    )
    geom_vline(xintercept = breakpoints, alpha = 0.8)
    geom_label_repel(
      aes(x = xmid, y = ymid, label = id),
      fill = alpha("white", 0.8),
      data = segments,
      max.overlaps = Inf,
      min.segment.length = 0,
      force = 5,
      direction = "both"
    )

  return(gg)
}


fit_splines <- function(
  response,
  explanatory,
  df = NULL,
  breakpoints = NULL,
  min_breakpoint = 50,
  intercept = TRUE
) {
  if (!is.null(df)) {
    explanatory <- df[[explanatory]]
    response <- df[[response]]
  }

  if (is.null(breakpoints)) {
    breakpoints <- find_segments(response, explanatory, plot_it = FALSE)$psi
  }

  breakpoints <- breakpoints[diff(c(0, breakpoints)) > min_breakpoint]

  features <- splines::bs(explanatory, knots = breakpoints)
  if (intercept) {
    fit <- lm(response ~ features)
  } else {
    fit <- lm(response ~ -1 + features)
  }
  fit_summary <- summary(fit)

  return(list("features" = features, "fit" = fit, "summary" = fit_summary))
}


#' Approximation of derivative.
forward_difference <- function(arr, order = 1, degree = 1) {
  n <- length(arr)

  for (i in seq_len(degree)) {
    f <- arr[(1 + order):n] - arr[1:(n - order)]
    # Pad left with zeros
    arr <- c(numeric(order), f)
  }

  return(arr)
}


find_slope_increasing <- function(yhat, time, order = 1) {
  d1 <- forward_difference(yhat, order = order) / order
  d2 <- forward_difference(d1, order = order) / order

  inflection <- which.max(d1)
  slope <- d1[inflection]
  inflection_value <- yhat[inflection]
  yintercept <- inflection_value + (time[inflection] * (-slope))

  start <- which.min(yhat[seq_len(inflection)])
  end <- which.max(yhat[inflection:length(yhat)]) + inflection
  start <- start + which.max(d2[start:inflection])
  end <- inflection + which.min(d2[inflection:end])

  return(list(
    inflection = time[inflection],
    d1 = d1,
    d2 = d2,
    slope = slope,
    yintercept = yintercept,
    inflection_value = inflection_value,
    start = time[start],
    end = time[end]
  ))
}


find_slope_decreasing <- function(yhat, time, order = 1) {
  d1 <- forward_difference(yhat, order = order) / order
  d2 <- forward_difference(d1, order = order) / order

  inflection <- which.min(d1)
  slope <- d1[inflection]
  inflection_value <- yhat[inflection]
  yintercept <- inflection_value + (time[inflection] * (-slope))

  start <- which.max(yhat[seq_len(inflection)])
  end <- which.min(yhat[inflection:length(yhat)]) + inflection
  start <- start + which.min(d2[start:inflection])
  end <- inflection + which.max(d2[inflection:end])


  return(list(
    inflection = time[inflection],
    d1 = d1,
    d2 = d2,
    slope = slope,
    yintercept = yintercept,
    inflection_value = inflection_value,
    start = time[start],
    end = time[end]
  ))
}


find_curve <- function(fit, features, time, increasing = TRUE, target = NULL) {
  coefs <- coefficients(fit)

  if (is.numeric(target)) {
    # This only has to be here to prevent
    # checking others, which raise errors.
  } else if (is.null(target)) {
    target <- seq_len(sum(names(coefs) != "(Intercept)"))
  } else if (target == "best") {
    su <- summary(fit)$coefficients
    target <- unname(which.max(abs(su[names(coefs) != "(Intercept)", "t value"])))
  } else if (target == "significant") {
    su <- summary(fit)$coefficients
    target <- unname(which(su[names(coefs) != "(Intercept)", "Pr(>|t|)"] < 1e-10))
  }
  yhat <- as.vector(coefs[paste0("features", target)] %*% t(features[, target]))

  if ("(Intercept)" %in% names(coefs)) {
    yhat <- yhat + coefs["(Intercept)"]
  }

  if (increasing) {
    slope <- find_slope_increasing(yhat, time)
  } else {
    slope <- find_slope_decreasing(yhat, time)
  }

  slope[["yhat"]] <- yhat
  slope[["target"]] <- target
  slope[["time"]] <- time
  return(slope)
}


find_spline_components <- function(fit, features, time) {
  coefs <- coefficients(fit)
  if ("(Intercept)" %in% names(coefs)) {
    d <- t(coefs[-1] * t(features))
    d <- d + coefs["(Intercept)"]
  } else {
    d <- t(coefs * t(features))
  }

  minmax <- c()
  time_ <- c()
  for (i in seq_along(coefs[-1])) {
    coef <- coefs[i + 1]
    if (coef < 0) {
      minmax <- c(minmax, i)
      time_ <- c(time_, which.min(d[, i]) - 1)
    } else {
      minmax <- c(minmax, i)
      time_ <- c(time_, which.max(d[, i]) - 1)
    }
  }
  time_ <- time[time_]

  minmax <- data.frame(
    features = as.character(seq_along(minmax)),
    time = time_,
    label = as.character(round(minmax))
  )

  d <- as.data.frame(d)
  d$time <- time
  return(list(component_modes = minmax, components = d))
}


plot_slope <- function(response, time, intercept, slope, inflection) {
  df <- data.frame(cbind(response, time))
  names(df) <- c("response", "time")

  time_labs <- df[["time"]]
  time_labs[time_labs != inflection] <- NA
  df[["label"]] <- as.character(time_labs)
  df[is.na(df[["label"]]), "label"] <- ""

  if (slope < 0) {
    hjust <- "left"
    vjust <- "top"
    form_x <- min(df[["time"]])
    form_y <- max(df[["response"]])
  } else {
    hjust <- "right"
    vjust <- "top"
    form_x <- max(df[["time"]])
    form_y <- max(df[["response"]])
  }

  gg <- ggplot(df, aes(x = time, y = response, label = label))
    geom_point(alpha = 0.6)
    geom_vline(xintercept = inflection, color = "royalblue", alpha = 0.8)
    geom_abline(
      intercept = intercept,
      slope = slope,
      color = "red",
      linewidth = 1.5,
      alpha = 0.6)
    geom_label_repel(
      max.overlaps = Inf,
      min.segment.length = 0,
      color = "black",
      fill = alpha("white", 0.8),
      force = 5,
      direction = "both")
    annotate(
      "label",
      x = form_x,
      y = form_y,
      label = sprintf("y ~ %0.2e + %0.2e * time", intercept, slope),
      hjust = hjust,
      vjust = vjust,
      color = "black",
      fill = alpha("white", 0.8)
    )
  return(gg)
}


plot_spline_knots <- function(response, fit, features, slope, time) {

  components <- find_spline_components(fit, features, time)
  component_modes <- components$component_modes
  components <- components$components

  target <- slope[["target"]]
  yhat <- slope[["yhat"]]

  components["spline"] <- as.vector(yhat)
  components["actual"] <- response
  components <- tidyr::pivot_longer(
    components,
    -time,
    names_to = "features",
    values_to = "response"
  )

  components <- left_join(components, component_modes, by = c("features", "time"))
  components[["features"]] <- factor(
    components[["features"]],
    labels = c(seq_len(ncol(features)), "spline", "actual"),
    levels = c(seq_len(ncol(features)), "spline", "actual")
  )
  components[is.na(components[["label"]]), "label"] <- ""

  gg <- ggplot(
    components,
    aes(x = time, y = response, color = features, label = label))
    layer(
      geom = "point",
      stat = "identity",
      position = "identity",
      data = components[components$features == "actual", ],
      params = list(color = "black", alpha = 0.3, size = 1))
    layer(
      geom = "line",
      stat = "identity",
      position = "identity",
      data = components[components$features == "spline", ],
      params = list(color = "red", alpha = 0.6, linewidth = 1.5))
    layer(
      geom = "line",
      stat = "identity",
      position = "identity",
      data = components[!components$features %in% c("spline", "actual"), ],
      show.legend = FALSE,
      params = list(alpha = 0.8))
    scale_color_manual(
      breaks = seq_len(ncol(features)),
      values = ifelse(seq_len(ncol(features)) %in% target, "royalblue", "darkgray"))
    geom_label_repel(
      max.overlaps = Inf,
      min.segment.length = 0,
      color = "black",
      fill = alpha("white", 0.8),
      force = 2,
      direction = "y")

  return(gg)
}


plot_user_prompt <- function(
  df,
  response,
  spl,
  curve,
  segments,
  intercept = NULL,
  inflection = NULL,
  slope = NULL
) {
  gg1 <- plot_segmented_lines(df[[response]], df[["time"]], segments)
  gg2 <- plot_spline_knots(df[[response]], spl$fit, spl$features, curve, df[["time"]])

  if (is.null(intercept) || is.null(inflection) || is.null(slope)) {
    intercept <- curve[["yintercept"]]
    inflection <- curve[["inflection"]]
    slope <- curve[["slope"]]
  }
  gg3 <- plot_slope(df[[response]], df[["time"]], intercept, slope, inflection)

  gg <- cowplot::plot_grid(
    gg1,
    gg2,
    gg3,
    nrow = 3,
    ncol = 1,
    rel_heights = c(3, 3, 3)
  )

  return(gg)
}


split_regex <- function(x) {
  x <- paste0(" ", x)
  re <- paste(
    "[[:digit:]]+[[:space:]]*:[[:space:]]*([[:digit:]]+|n)",
    "[[:digit:]]+[[:space:]]*:",
    ":[[:space:]]*([[:digit:]]+|n)",
    "[[:space:]]+",
    ",",
    sep = "|"
  )
  split.pos <- gregexpr(re, x, perl = TRUE)[[1]]
  split.length <- attr(split.pos, "match.length")
  split.start <- sort(c(split.pos, split.pos + split.length))
  split.end <- c(split.start[-1] - 1, nchar(x))
  s <- substring(x, split.start, split.end)
  s <- s[!s %in% c("", " ", ",")]
  s <- sub(pattern = "[[:space:]]+", replacement = "", s)
  return(s)
}


try_parse_numeric <- function(s, ncomponents = NULL) {
  suppressWarnings(s_ <- as.numeric(s))
  if (any(is.na(s_))) {
    return(NULL)
  } else {
    return(s_)
  }
}


try_parse_range <- function(s, ncomponents) {
  s <- tolower(s)
  s_ <- strsplit(s, ":")[[1]]
  if (length(s_) == 0) {
    return(NULL)
  } else if (length(s_) == 1) {
    if (s_ == "n") {
      s_ <- ncomponents
    }
    s_int <- try_parse_numeric(s_)
    if (is.na(s_int) || is.null(s_int)) {
      warning(sprintf("Could not interpret '%s' as a number", s_))
      return(NULL)
    } else {
      return(s_int)
    }
  } else if (length(s_) != 2) {
    warning(sprintf("Couldn't parse '%s' as a range. Got %d elements.", s, length(s_)))
    return(NULL)
  }

  s_ <- replace(s_, s_ == "n", ncomponents)
  s_nums <- try_parse_numeric(s_)

  if (any(is.na(s_nums))) {
    warning(sprintf("Got non-numbers in range expression %s", s))
    return(NULL)
  }

  return(seq(s_nums[1], s_nums[2]))
}


try_parse_ys <- function(splitx, ncomponents = NULL) {
  if (length(splitx) == 0) {
    return(NULL)
  }

  valid <- c(
    "y" = "yes", "o" = "yes",
    "yes" = "yes", "oui" = "yes",
    "s" = "skip", "skip" = "skip",
    "b" = "best", "best" = "best",
    "q" = "quit", "quit" = "quit",
    "e" = "quit", "exit" = "quit"
  )
  response <- splitx[1]

  if (response %in% names(valid)) {
    response <- valid[response]
    return(unname(response))
  }

  return(NULL)
}


try_parse_response <- function(splitx, ncomponents, size, nsegments) {
  if (length(splitx) == 0) {
    return(NULL)
  }

  if (splitx[1] %in% c("c", "comp", "component", "components")) {
    splitx <- splitx[-1]
    action <- "component"
    had_action <- TRUE
  } else if (splitx[1] %in% c("r", "range")) {
    splitx <- splitx[-1]
    action <- "range"
    had_action <- TRUE
  } else if (splitx[1] %in% c("g", "segment", "segmented")) {
    splitx <- splitx[-1]
    action <- "segment"
    had_action <- TRUE
  } else {
    action <- "component"
    had_action <- FALSE
  }

  ys <- try_parse_ys(splitx)

  if (!is.null(ys)) {
    if (had_action) {
      warning(sprintf("You cannot specify range or components and also %s.\n", ys))
      return(NULL)
    } else if (length(splitx) > 1) {
      warning(sprintf("You specified '%s', but there are other commands after it.\nPlease remove them an try again.\n", ys))
      return(NULL)
    } else {
      return(list("action" = ys, "values" = NULL))
    }
  }

  if (action == "range") {
    values <- lapply(splitx, FUN = function(x) {try_parse_range(x, size)})
  } else {
    values <- lapply(splitx, FUN = function(x) {try_parse_range(x, ncomponents)})
  }

  if (any(vapply(values, FUN = is.null, FUN.VALUE = TRUE))) {
    return(NULL)
  }

  values <- as.numeric(unlist(values))

  if (action == "ERROR") {
    warning("Sorry, this shouldn't happen but we got an unhandled error, parsing your input.\n")
    return(NULL)
  }

  if (action == "range") {
    if (length(values) != 2) {
      warning(sprinf("When specifying a range, you must provide two number for the first and last times to re-run the analysis from. Here we got %d numbers.\n", length(values)))
      return(NULL)
    }

    if (values[1] > values[2]) {
      warning(sprintf("The range start value '%d' is bigger than the end value '%d'. I'm flipping them.\n", values[1], values[2]))
      values <- c(values[2], values[1])
    }

    if (values[2] > size) {
      warning(sprintf("The range end value '%d' is bigger than the length of the time points %d. I'm truncating it.\n", values[2], size))
      values[2] <- size
    }
  } else if (action == "segment") {
    if (length(values) != 1) {
      warning(sprinf("When specifying segment slope, you must provide only one number. Here we got %d numbers.\n", length(values)))
      return(NULL)
    }
    if ((values[1] > nsegments) | (values[1] < 1)) {
      warning(sprintf("The specified segment '%d' is outside the valid range of segments (1:%d).\n", values[1], nsegments))
      return(NULL)
    }
  } else if (action == "component") {
    values <- sort(unique(values))
    if (any(values > ncomponents)) {
      print(values)
      warning(sprintf("The values %s are bigger than the number of spline components %d. I'm removing them.\n", paste(values[values > ncomponents], collapse = ", "), ncomponents))
      values <- values[values <= ncomponents]
    }
  }
  if (length(values) == 0) {
    warning("After filtering, we didn't get any numbers. This shouldn't really happen, but try again.")
    return(NULL)
  }

  return(list(action = action, values = values))
}


get_action <- function(ncomponents, size, nsegments) {
  parsed_response <- NULL
  while (is.null(parsed_response)) {
    cat("Please decide what to do.\n")
    cat("- [y]es, [o]ui to accept the slope.\n")
    cat("- [s]kip to ignore this one because it's unreliable.\n")
    cat("- [[r]ange <start> <end>] to restrict the start and end times (and refit the spline).\n")
    cat("- [[c]omponent <int> <int>:<int>] to select spline components.\n")
    cat("- se[g]ment <int> to select the slope from one of the segments.")
    cat("- [q]uit to exit.\n\n")
    response <- tolower(readline("INPUT: "))

    cat("\n")
    parsed_response <- try_parse_response(
      split_regex(response),
      ncomponents,
      size,
      nsegments
    )
  }
  return(parsed_response)
}


select_slopes <- function(
  df,
  response,
  increasing = NULL,
  interactive = TRUE,
  start = NULL,
  end = NULL,
  target = NULL,
  min_segment = 50
) {
  breakpoints <- find_segments(df[[response]], df[["time"]], plot_it = FALSE)

  segments_df <- find_segmented_lines(breakpoints, min(df[["time"]]), max(df[["time"]]), min_segment = min_segment)

  spl <- fit_splines(df[[response]], df[["time"]], breakpoints = breakpoints$psi, intercept = TRUE)

  if (is.null(increasing)) {
    increasing <- response == "lesion_area"
  }

  curve <- find_curve(spl$fit, spl$features, df[["time"]], increasing = increasing, target = NULL)
  user <- NULL
  # %in% doesn't work with NULL, so using a string instead
  action <- "NULL"

  if (is.null(start)) {
    start <- min(df[["time"]])
  }

  if (is.null(end)) {
    end <- max(df[["time"]])
  }

  rdf <- df[(df[["time"]] >= start) & (df[["time"]] <= end), ]

  slope <- list(
    intercept = curve[["yintercept"]],
    inflection = curve[["inflection"]],
    slope = curve[["slope"]]
  )

  if (!interactive) {
    gg <- plot_user_prompt(
      rdf,
      response,
      spl,
      curve,
      segments_df,
      slope = slope$slope,
      intercept = slope$intercept,
      inflection = slope$inflection
    )
    print(gg)
    return(list("plot" = gg, "spline" = spl, "curve" = curve))
  }

  while (!(action %in% c("yes", "skip"))) {
    gg <- plot_user_prompt(
      rdf,
      response,
      spl,
      curve,
      segments_df,
      slope = slope$slope,
      intercept = slope$intercept,
      inflection = slope$inflection
    )
    print(gg)

    user <- get_action(ncol(spl$features), max(df[["time"]]), max(segments_df[["id"]]))

    if (is.null(user)) {
      next
    } else {
      action <- user[["action"]]
    }

    if (action == "range") {
      start <- user[["values"]][1]
      end <- user[["values"]][2]
      rdf <- df[(df[["time"]] >= start) & (df[["time"]] <= end), ]
      breakpoints <- find_segments(rdf[[response]], rdf[["time"]], plot_it = FALSE)
      segments_df <- find_segmented_lines(breakpoints, min(rdf[["time"]]), max(rdf[["time"]]), min_segment = min_segment)
      spl <- fit_splines(rdf[[response]], rdf[["time"]], breakpoints = breakpoints$psi, intercept = TRUE)

      target <- NULL
      curve <- find_curve(
        spl$fit,
        spl$features,
        rdf[["time"]],
        increasing = increasing,
        target = target
      )
      slope <- list(
        intercept = curve[["yintercept"]],
        inflection = curve[["inflection"]],
        slope = curve[["slope"]]
      )
    } else if (action == "component") {
      target <- user[["values"]]
      curve <- find_curve(
        spl$fit,
        spl$features,
        rdf[["time"]],
        increasing = increasing,
        target = target
      )
      slope <- list(
        intercept = curve[["yintercept"]],
        inflection = curve[["inflection"]],
        slope = curve[["slope"]]
      )
    } else if (action == "segment") {
      index <- which(segments_df["id"] == user[["values"]])
      if (length(index) != 1) {
        stop("This shouldn't happen.")
      }
      slope <- list(
        intercept = segments_df[index, "intercept"],
        inflection = segments_df[index, "xmid"],
        slope = segments_df[index, "slope"]
      )
    } else if (action == "quit") {
      return(NULL)
    }
  }

  return(list("plot" = gg, "decision" = action, "intercept" = slope$intercept, "midpoint" = slope$inflection, "slope" = slope$slope))
}


process_file <- function(df, outfile, response, min_segment = 20) {
  if (!is.data.frame(df)) {
    df <- readr::read_table(df)
  }

  if (file.exists(outfile)) {
    append <- TRUE
    outdf <- readr::read_table(outfile)
    done <- unique(outdf[["id"]])
    ids <- unique(df[["id"]])

    ids <- setdiff(ids, done)
  } else {
    append <- FALSE
    outdf <- data.frame(matrix(ncol = 6, nrow = 0))
    colnames(outdf) <- c("id", "leaf_area_t0", "midpoint", "intercept", "slope", "decision")
    ids <- unique(df[["id"]])
  }

  for (id_ in ids) {
    sdf <- df[df[["id"]] == id_, ]
    sl <- select_slopes(sdf, response, interactive = TRUE, min_segment = min_segment)

    if (is.null(sl)) {
      return()
    }

    leaf_area_t0 <- unname(as.vector(sdf[which.min(sdf[["time"]]), "leaf_area"]))[[1]]

    outdf <- tibble(
      id = id_,
      leaf_area_t0 = leaf_area_t0,
      midpoint = sl$midpoint,
      intercept = sl$intercept,
      slope = sl$slope,
      decision = sl$decision
    )

    readr::write_tsv(outdf, outfile, append = append)
    append <- FALSE
  }
}
