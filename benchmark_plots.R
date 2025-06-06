#setting current working directory as working directory
setwd('C:/Users/Muskaan Gupta/Documents/My Projects/Glasgow Computational Biology Hackathon 2025')

#calling libraries
library(reshape2)
library(ggplot2)
library(devEMF)

#loading the data
raw_data = read.table(header = TRUE, file = './sequence_identity_benchmark_data.csv', sep = ',')

#rearranging columns for easier understanding
print(colnames(raw_data))
new_colnames = c('sequence_identity', 'joe_file_size', 'joseph_file_size', 'ifed_file_size', 'fasta_file_size', 'joe_node_number', 'joseph_node_number', 'ifed_node_number','joe_relationship_number', 'joseph_relationship_number', 'ifed_relationship_number', 'joe_file_time', 'joseph_file_time', 'ifed_file_time')
raw_data = raw_data[,new_colnames]

#labels:
#joe is 'compressed_edges'
#joseph is 'many_edges'
#ifed is 'many_nodes'
joe = 'Compressed Edges'
joseph = 'Many Edges'
ifed = 'Many Nodes'

#plotting the following plots
#1: file size
#2: node number
#3: relationship number
#4: file time

#plotting file size
file_size_data = melt(raw_data[,1:5], id.vars = 'sequence_identity')
file_size_data$variable = factor(file_size_data$variable, levels = c("joe_file_size", "joseph_file_size", "ifed_file_size", "fasta_file_size"),
                  labels = c(joe, joseph, ifed, 'FASTA')
)

plot1 = ggplot(file_size_data, aes(x = variable, y = value, colour = variable, fill = variable)) +
  geom_col(position = 'dodge', color = "black") +
  facet_grid( ~ sequence_identity, switch = "x") + 
  theme_bw() + 
  ggtitle('File Size Comparison') + 
  xlab('Approaches') + 
  ylab('File Size') +
  guides(fill=guide_legend(title="Approaches"))

#plotting node number
node_number_data = cbind(raw_data[,1], raw_data[,6:8])
names(node_number_data)[names(node_number_data) == 'raw_data[, 1]'] = 'sequence_identity'
node_number_data = melt(node_number_data, id.vars = 'sequence_identity')
node_number_data$variable = factor(node_number_data$variable, levels = c("joe_node_number", "joseph_node_number", "ifed_node_number"),
                                 labels = c(joe, joseph, ifed)
)

plot2 = ggplot(node_number_data, aes(x = variable, y = value, colour = variable, fill = variable)) +
  geom_col(position = 'dodge', color = "black") +
  facet_grid( ~ sequence_identity, switch = "x") + 
  theme_bw() + 
  ggtitle('Node Number Comparison') + 
  xlab('Approaches') + 
  ylab('Node Numbers') +
  guides(fill=guide_legend(title="Approaches"))

#plotting relationship number
relationship_number_data = cbind(raw_data[,1], raw_data[,9:11])
names(relationship_number_data)[names(relationship_number_data) == 'raw_data[, 1]'] = 'sequence_identity'
relationship_number_data = melt(relationship_number_data, id.vars = 'sequence_identity')
relationship_number_data$variable = factor(relationship_number_data$variable, levels = c("joe_relationship_number", "joseph_relationship_number", "ifed_relationship_number"),
                                   labels = c(joe, joseph, ifed)
)

plot3 = ggplot(relationship_number_data, aes(x = variable, y = value, colour = variable, fill = variable)) +
  geom_col(position = 'dodge', color = "black") +
  facet_grid( ~ sequence_identity, switch = "x") + 
  theme_bw() + 
  ggtitle('Relationship Number Comparison') + 
  xlab('Approaches') + 
  ylab('Relationship Numbers') +
  guides(fill=guide_legend(title="Approaches"))

#plotting file time
file_time_data = cbind(raw_data[,1], raw_data[,12:14])
names(file_time_data)[names(file_time_data) == 'raw_data[, 1]'] = 'sequence_identity'
file_time_data = melt(file_time_data, id.vars = 'sequence_identity')
file_time_data$variable = factor(file_time_data$variable, levels = c("joe_file_time", "joseph_file_time", "ifed_file_time"),
                                           labels = c(joe, joseph, ifed)
)
#dropping NAs
file_time_data = na.omit(file_time_data)

plot4 = ggplot(file_time_data, aes(x = variable, y = value, colour = variable, fill = variable)) +
  geom_col(position = 'dodge', color = "black") +
  facet_grid( ~ sequence_identity, switch = "x") + 
  theme_bw() + 
  ggtitle('File Time Comparison') + 
  xlab('Approaches') + 
  ylab('File Times') +
  guides(fill=guide_legend(title="Approaches"))

#saving plots - NOT USING THIS. messes up fonts and labels
#ggsave("file_size.emf", plot = plot1, width = 30, dpi = 300,limitsize = FALSE, device = {function(filename, ...) devEMF::emf(file = filename, ...)})
#ggsave("node_number.emf", plot = plot2, width = 13 ,device = {function(filename, ...) devEMF::emf(file = filename, ...)})
#ggsave("relationship_number.emf", plot = plot3, width = 13 ,device = {function(filename, ...) devEMF::emf(file = filename, ...)})
#ggsave("file_time.emf", plot = plot4, width = 13 ,device = {function(filename, ...) devEMF::emf(file = filename, ...)})