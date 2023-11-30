library(sjmisc)
library(dplyr)
library(tidyr)
library(stringr)
library(ggplot2)
source("/home/jelman/netshare/K/code/misc/summarySE.R")
source("/home/jelman/netshare/K/code/misc/summarySEwithin.R")
source("/home/jelman/netshare/K/code/misc/normDataWithin.R")

df = read_sas("/home/jelman/netshare/M/PSYCH/KREMEN/VETSA DATA FILES_852014/PUPILLOMETRY V2 CLEAN DATA_852014/digitspancombo852014.sas7bdat")
mcidf = read.csv("/home/jelman/netshare/K/data/VETSA_Demographics/VETSA2_MCI.csv")
mcidf = mcidf %>% select(vetsaid, rMCI_cons_v2)
mcidf = mcidf[!is.na(mcidf$rMCI_cons_v2),]
mcidf$rMCI_consgrp_v2 = mcidf$rMCI_cons_v2
mcidf[mcidf$rMCI_cons_v2==3 | mcidf$rMCI_cons_v2==4 ,"rMCI_consgrp_v2"] = 3
mcidf$rMCI_consgrp_v2 = factor(mcidf$rMCI_consgrp_v2, labels=c("CN", "S-naMCI", "S-aMCI", "M-MCI"))
# Create wave forms for Average pupildilation
dfAvg = df %>% select(vetsaid, contains("AvgDSWF"), -contains("Diff"))

dfAvgtidy = dfAvg %>% 
  gather(key, Diameter, contains("AvgDSWF")) %>% 
  separate(key, into=c("Condition","Time"), sep="AvgDSWF") %>%
  separate(Time, into=c("StartTime","EndTime"), sep="_") %>%
  mutate(Condition=sub("DS", "", Condition)) %>%
  right_join(mcidf[c("vetsaid","rMCI_consgrp_v2")], by="vetsaid")

dfAvgSummary = summarySE(dfAvgtidy, measurevar="Diameter", groupvars=c("rMCI_consgrp_v2","Condition", "EndTime"), na.rm=T)
dfAvgSummary$EndTime = as.integer(dfAvgSummary$EndTime)
dfAvgSummary = dfAvgSummary[order(dfAvgSummary$EndTime),]

# Plot
ggplot(data=dfAvgSummary, aes(x=EndTime, y=Diameter, color=Condition, group=Condition)) + facet_wrap("rMCI_consgrp_v2") +
  scale_colour_brewer(name = "Condition\n(# digits)", palette="Set1") +  geom_line(size=1.5) + geom_point(size=2) + 
  xlab("Seconds") + ylab("Pupil Diameter (mm)") + theme_bw(20)
ggsave("/home/jelman/Dropbox/VETSA_Jeremy/Articles_InPrep/pupillometry/manuscript/MCI Pupil Paper/PupilDilation_Waveforms.png",dpi=300)

write.csv(dfAvgSummary, "/home/jelman/netshare/K/data/Pupillometry/VETSA2/PupilDilationAvg_PerSecond.csv", row.names = F)


# Create wave forms for difference in dilation from baseline
dfDiff = df %>% select(vetsaid, contains("Diff"))
dfDifftidy = dfDiff %>% 
  gather(key, Diameter, contains("AvgDSWF")) %>% 
  separate(key, into=c("Condition","Time"), sep="AvgDSWF") %>%
  separate(Time, into=c("StartTime","EndTime"), sep="_") %>%
  mutate(EndTime=sub("Diff", "", EndTime)) %>%
  mutate(Condition=sub("DS", "", Condition)) %>%
  right_join(mcidf[c("vetsaid","rMCI_consgrp_v2")], by="vetsaid")

dfDiffSummary = summarySE(dfDifftidy, measurevar="Diameter", groupvars=c("rMCI_consgrp_v2", "Condition", "EndTime"), na.rm=T)

dfDiffSummary = summarySEwithin(dfDifftidy, 
                                      measurevar="Diameter", 
                                      idvar="vetsaid", 
                                      withinvars=c("EndTime","Condition"),
                                      betweenvars="rMCI_consgrp_v2",
                                      na.rm=TRUE)

dfDiffSummary$EndTime = as.integer(dfDiffSummary$EndTime)
dfDiffSummary = dfDiffSummary[order(dfDiffSummary$EndTime),]
dfDiffSummary = dfDiffSummary[!is.na(dfDiffSummary$Condition),]

#Plot by group
ggplot(data=dfDiffSummary, aes(x=EndTime, y=Diameter, color=Condition, group=Condition)) + facet_wrap("rMCI_consgrp_v2") +
  geom_line(size=1.5) + geom_point(size=2) +
  scale_color_brewer(name = "Condition\n(# digits)", palette="Set1") +
  xlab("Seconds") + ylab(expression(paste(Delta, " Pupil Diameter (mm)"))) + theme_bw(20)

ggsave("/home/jelman/Dropbox/VETSA_Jeremy/Articles_InPrep/pupillometry/manuscript/MCI Pupil Paper/PupilWaveforms_GroupFacets.tiff",dpi=300)

# Plot by condition
ggplot(data=dfDiffSummary, aes(x=EndTime, y=Diameter, color=rMCI_consgrp_v2, group=rMCI_consgrp_v2)) + facet_wrap("Condition") +
  geom_line(size=1.5) + geom_point(size=2) + 
  scale_color_brewer(name = "Group", palette="Set1") +
  xlab("Seconds") + ylab(expression(paste(Delta, " Pupil Diameter (mm)"))) + theme_bw(20)

ggsave("/home/jelman/Dropbox/VETSA_Jeremy/Articles_InPrep/pupillometry/manuscript/MCI Pupil Paper/PupilWaveforms_ConditionFacets.tiff",dpi=300)


write.csv(dfDiffSummary, "/home/jelman/Dropbox/VETSA_Jeremy/Articles_InPrep/pupillometry/manuscript/MCI Pupil Paper/PupilDilationDiff_PerSecond.csv", row.names = F)
