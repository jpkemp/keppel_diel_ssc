library(mgcv)
library(FSSgam)

assign_data_to_parent_env <- function(data) {
    use.dat <<- data
}

soundtrap_model_set <- function(savedir, name) { # expects an existing model.set
    out.list <- FSSgam::fit.model.set(model.set, max.models=800, parallel = TRUE)
    out.all <- list()
    mod.table <- out.list$mod.data.out  # look at the model selection table
    mod.table <- mod.table[order(mod.table$AICc), ]
    mod.table$cumsum.wi <- cumsum(mod.table$wi.AICc)
    var.imp <- list(out.list$variable.importance$aic$variable.weights.raw) #Or importance score weighted by r2
    out.all <- c(out.all,list(mod.table))

    best.model.name = as.character(mod.table$modname[1])
    if(best.model.name != "null"){
        par(mfrow = c(3, 1), mar = c(9, 4, 3, 1))
        best.model = out.list$success.models[[best.model.name]]
        png(file = paste(savedir, paste(name, best.model.name, "mod_fits.png", sep = "_"), sep = "/"))
        plot(best.model,all.terms = T, pages = 1, residuals = T, pch = 16)
        mtext(side = 2, text = "test", outer = F)
        dev.off()
        png(file = paste(savedir, paste(name, best.model.name, "qq.png", sep = "_"), sep = "/"))
        mgcv::qq.gam(best.model)
        dev.off()
        # png(file = paste(savedir, paste(name, best.model.name, "vis", sep = "_"), sep = "/"))
        # mgcv::vis.gam(best.model)
        # dev.off()
    }

    # Save model fits and importance scores
    all.mod.fits   <- do.call("rbind",out.all)
    all.var.imp    <- do.call("rbind",var.imp)

    write.csv(all.mod.fits, file = paste(savedir, paste("all.mod.fits", name, ".csv", sep = "_"), sep = "/"))
    write.csv(all.var.imp, file = paste(savedir, paste("all.var.imp", name, ".csv", sep = "_"), sep = "/"))
}
