import pygad
import numpy as np
import random
from math import sqrt

class CustomGA_binary(pygad.GA):
    def __init__(self, num_generations, sol_per_pop, num_parents_mating, num_genes, fitness_func, init_range_low,
                 init_range_high, mutation_num_genes, parent_selection_type, crossover_type, mutation_type,
                 keep_elitism, K_tournament, random_mutation_max_val, random_mutation_min_val, logger=None,
                 on_generation=None, parallel_processing=None):

        supported_crossover_types = [
            "single_point", "two_points", "uniform", "scattered", "three_point", "grainy",
            "RRC", "crossover_by_dominance", "DIS", "adaption_weighted_cross"
        ]
        
        if crossover_type not in supported_crossover_types:
            raise TypeError("Undefined crossover type. The assigned value to the crossover_type parameter "
                            "({crossover_type}) does not refer to one of the supported crossover types which are: "
                            "{supported_crossover_types}.".format(crossover_type=crossover_type,
                                                                   supported_crossover_types=", ".join(
                                                                       supported_crossover_types)))

        #nie jestem pewna czy to dziala ale inne proby nie dzialaly na 100% XD
        self.original_crossover_type = crossover_type

        if crossover_type not in ["single_point", "two_points", "uniform", "scattered"]:
            crossover_type = "uniform"

        super().__init__(num_generations=num_generations,
                         sol_per_pop=sol_per_pop,
                         num_parents_mating=num_parents_mating,
                         num_genes=num_genes,
                         fitness_func=fitness_func,
                         init_range_low=init_range_low,
                         init_range_high=init_range_high,
                         mutation_num_genes=mutation_num_genes,
                         parent_selection_type=parent_selection_type,
                         crossover_type=crossover_type,
                         mutation_type=mutation_type,
                         keep_elitism=keep_elitism,
                         K_tournament=K_tournament,
                         random_mutation_max_val=random_mutation_max_val,
                         random_mutation_min_val=random_mutation_min_val,
                         logger=logger,
                         on_generation=on_generation,
                         parallel_processing=parallel_processing)
        
    def three_point_crossover(self, parents, offspring_size):
        offspring = np.empty(offspring_size, dtype=parents.dtype)
        for k in range(offspring_size[0]):
            parent1_idx = k % parents.shape[0]
            parent2_idx = (k + 1) % parents.shape[0]
            parent1 = parents[parent1_idx]
            parent2 = parents[parent2_idx]
            
            crossover_points = sorted(random.sample(range(1, parents.shape[1]), 3))
            
            child1 = np.concatenate((parent1[:crossover_points[0]],
                                    parent2[crossover_points[0]:crossover_points[1]],
                                    parent1[crossover_points[1]:crossover_points[2]],
                                    parent2[crossover_points[2]:]))
            child2 = np.concatenate((parent2[:crossover_points[0]],
                                    parent1[crossover_points[0]:crossover_points[1]],
                                    parent2[crossover_points[1]:crossover_points[2]],
                                    parent1[crossover_points[2]:]))

            offspring[k] = child1 if k % 2 == 0 else child2
        return offspring

    def grainy_crossover(self, parents, offspring_size):
        offspring = np.empty(offspring_size, dtype=parents.dtype)
        for k in range(offspring_size[0]):
            parent1_idx = k % parents.shape[0]
            parent2_idx = (k + 1) % parents.shape[0]
            parent1 = parents[parent1_idx]
            parent2 = parents[parent2_idx]
            
            child1, child2 = parent1.copy(), parent2.copy()
            for j in range(0, parents.shape[1], self.grain_size):
                if random.random() <= 0.5:
                    child1[j] = parent1[j]
                    child2[j] = parent2[j]
                else:
                    child1[j] = parent2[j]
                    child2[j] = parent1[j]

            offspring[k] = child1 if k % 2 == 0 else child2
        return offspring
    
    def RRC(self, parents, offspring_size):
        offspring = np.empty(offspring_size, dtype=parents.dtype)
        n = offspring_size[0]
        for i in range(n):
            parent1_idx = i % parents.shape[0]
            parent2_idx = (i + 1) % parents.shape[0]
            A = parents[parent1_idx]
            B = parents[parent2_idx]
            
            S = np.where(A == B, A, None)
            mask_shape = A.shape
            mask = np.where(S != None, S, np.where(np.random.uniform(0, 1, size=mask_shape) <= 0.5, 1, 0))
            C = np.where(S != None, S, mask)
            D = np.where(S != None, S, np.where(np.random.uniform(0, 1, size=mask_shape) <= 0.5, 1, 0))
            
            offspring[i] = C if i % 2 == 0 else D
        return offspring

    def crossover_by_dominance(self, parents, offspring_size):
        offspring = np.empty(offspring_size, dtype=parents.dtype)
        for k in range(offspring_size[0]):
            parent_A_idx = k % parents.shape[0]
            parent_B_idx = (k + 1) % parents.shape[0]
            parent_A = parents[parent_A_idx]
            parent_B = parents[parent_B_idx]

            mask_A = np.random.randint(0, 2, size=parent_A.shape)
            mask_B = np.random.randint(0, 2, size=parent_B.shape)

            child_C = parent_A.copy()
            child_D = parent_B.copy()

            for i in range(len(parent_A)):
                if mask_B[i] == 1 and mask_A[i] == 0:
                    child_C[i] = parent_B[i]
                if mask_B[i] == 0 and mask_A[i] == 1:
                    child_D[i] = parent_A[i]

            offspring[k] = child_C if k % 2 == 0 else child_D
        return offspring

    def DIS(self, parents, offspring_size):
        offspring = np.empty(offspring_size, dtype=parents.dtype)
        number_of_features = parents.shape[1]
        q = offspring_size[1]

        for k in range(offspring_size[0]):
            ind1_idx = k % parents.shape[0]
            ind2_idx = (k + 1) % parents.shape[0]
            ind1 = parents[ind1_idx]
            ind2 = parents[ind2_idx]

            size = len(ind1[0])
            new_ind = []
            for feature in range(number_of_features):
                new_gene = []
                for i in range(q):
                    if ind1[feature][i] != ind2[feature][i]:
                        new_gene.append(ind1[feature][i])
                    else:
                        new_gene.append(np.random.randint(0, 2))
                for i in range(q, size):
                    if ind1[feature][i] != ind2[feature][i]:
                        new_gene.append(ind2[feature][i])
                    else:
                        new_gene.append(np.random.randint(0, 2))
                new_ind.append(np.array(new_gene))

            offspring[k] = np.array(new_ind)
        return offspring
    
    #TODO krzyzowanie Wojtka (:

    def crossover(self, parents, offspring_size):
        if self.original_crossover_type == "three_point":
            return self.three_point_crossover(parents, offspring_size)
        elif self.original_crossover_type == "grainy":
            return self.grainy_crossover(parents, offspring_size)
        elif self.original_crossover_type == "RRC":
            return self.RRC(parents, offspring_size)
        elif self.original_crossover_type == "crossover_by_dominance":
            return self.crossover_by_dominance(parents, offspring_size)
        elif self.original_crossover_type == "DIS":
            return self.DIS(parents, offspring_size)
        # elif self.original_crossover_type == "adaption_weighted_cross":
        #     return self.adaption_weighted_cross(parents, offspring_size)
        else:
            return super().crossover(parents, offspring_size)

class CustomGA_real(pygad.GA):
    def __init__(self, num_generations, sol_per_pop, num_parents_mating, num_genes, fitness_func, init_range_low,
                 init_range_high, mutation_num_genes, parent_selection_type, crossover_type, mutation_type,
                 keep_elitism, K_tournament, random_mutation_max_val, random_mutation_min_val, logger=None,
                 on_generation=None, parallel_processing=None):

        supported_crossover_types = [
            "single_point", "two_points", "uniform", "scattered", "arithmetic", "linear", "alpha_mixed",
            "alpha_beta_mixed", "average", "crossover_HX", "SX_version1", "SX_version2", "f1_PAX",
            "fitness_weighted_cross_for_real_numbers"
        ]
        
        if crossover_type not in supported_crossover_types:
            raise TypeError("Undefined crossover type. The assigned value to the crossover_type parameter "
                            "({crossover_type}) does not refer to one of the supported crossover types which are: "
                            "{supported_crossover_types}.".format(crossover_type=crossover_type,
                                                                   supported_crossover_types=", ".join(
                                                                       supported_crossover_types)))

        self.original_crossover_type = crossover_type

        if crossover_type not in ["single_point", "two_points", "uniform", "scattered"]:
            crossover_type = "uniform"

        super().__init__(num_generations=num_generations,
                         sol_per_pop=sol_per_pop,
                         num_parents_mating=num_parents_mating,
                         num_genes=num_genes,
                         fitness_func=fitness_func,
                         init_range_low=init_range_low,
                         init_range_high=init_range_high,
                         mutation_num_genes=mutation_num_genes,
                         parent_selection_type=parent_selection_type,
                         crossover_type=crossover_type,
                         mutation_type=mutation_type,
                         keep_elitism=keep_elitism,
                         K_tournament=K_tournament,
                         random_mutation_max_val=random_mutation_max_val,
                         random_mutation_min_val=random_mutation_min_val,
                         logger=logger,
                         on_generation=on_generation,
                         parallel_processing=parallel_processing)
           
    def arithmetic_crossover(self, parents, offspring_size):
        offspring = np.empty(offspring_size, dtype=parents.dtype)
        for k in range(offspring_size[0]):
            parent1_idx = k % parents.shape[0]
            parent2_idx = (k + 1) % parents.shape[0]
            parent1 = parents[parent1_idx]
            parent2 = parents[parent2_idx]
            
            alpha = np.random.uniform(0, 1)
            offspring[k] = alpha * parent1 + (1 - alpha) * parent2
            
        return offspring

    def linear_crossover(self, parents, offspring_size):
        offspring = np.empty(offspring_size, dtype=parents.dtype)
        for k in range(offspring_size[0]):
            parent1_idx = k % parents.shape[0]
            parent2_idx = (k + 1) % parents.shape[0]
            parent1 = parents[parent1_idx]
            parent2 = parents[parent2_idx]
            
            n = len(parent1)
            Z = parent1 / 2 + parent2 / 2
            V = parent1 * 3 / 2 - parent2 / 2
            W = -parent1 / 2 + parent2 * 3 / 2
            
            vectors = [Z, V, W]
            fitness_values = [self.evaluate_subject(v) for v in vectors]
            best_index = np.argmax(fitness_values)
            
            offspring[k] = vectors[best_index]
            
        return offspring

    def alpha_mixed_crossover(self, parents, offspring_size):
        offspring = np.empty(offspring_size, dtype=parents.dtype)
        for k in range(offspring_size[0]):
            parent1_idx = k % parents.shape[0]
            parent2_idx = (k + 1) % parents.shape[0]
            parent1 = parents[parent1_idx]
            parent2 = parents[parent2_idx]
            
            n = len(parent1)
            child1 = np.empty(n)
            child2 = np.empty(n)
            alpha = random.random()
            
            for i in range(n):
                d = parent1[i] - parent2[i]
                min_value = min(parent1[i], parent2[i]) - alpha * d
                max_value = max(parent1[i], parent2[i]) + alpha * d
                
                child1[i] = np.random.uniform(min_value, max_value)
                child2[i] = np.random.uniform(min_value, max_value)
            
            offspring[k] = child1 if k % 2 == 0 else child2
            
        return offspring

    def alpha_beta_mixed_crossover(self, parents, offspring_size):
        offspring = np.empty(offspring_size, dtype=parents.dtype)
        for k in range(offspring_size[0]):
            parent1_idx = k % parents.shape[0]
            parent2_idx = (k + 1) % parents.shape[0]
            parent1 = parents[parent1_idx]
            parent2 = parents[parent2_idx]
            
            n = len(parent1)
            child1 = np.empty(n)
            child2 = np.empty(n)
            alpha = random.random()
            beta = random.random()
            
            for i in range(n):
                d = parent1[i] - parent2[i]
                if parent1[i] <= parent2[i]:
                    min_value = parent1[i] - alpha * d
                    max_value = parent2[i] + beta * d
                else:
                    min_value = parent2[i] - beta * d
                    max_value = parent1[i] + alpha * d
                
                child1[i] = np.random.uniform(min_value, max_value)
                child2[i] = np.random.uniform(min_value, max_value)
            
            offspring[k] = child1 if k % 2 == 0 else child2
            
        return offspring

    def average_crossover(self, parents, offspring_size):
        offspring = np.empty(offspring_size, dtype=parents.dtype)
        for k in range(offspring_size[0]):
            parent1_idx = k % parents.shape[0]
            parent2_idx = (k + 1) % parents.shape[0]
            parent1 = parents[parent1_idx]
            parent2 = parents[parent2_idx]
            
            offspring[k] = (parent1 + parent2) / 2
            
        return offspring

    def crossover_HX(self, parents, offspring_size):
        offspring = np.empty(offspring_size, dtype=parents.dtype)
        for k in range(offspring_size[0]):
            parent1_idx = k % parents.shape[0]
            parent2_idx = (k + 1) % parents.shape[0]
            parent1 = parents[parent1_idx]
            parent2 = parents[parent2_idx]
            
            alpha = random.random()
            if self.evaluate_subject(parent1) >= self.evaluate_subject(parent2):
                offspring[k] = [alpha * (p2 - p1) + p2 for p1, p2 in zip(parent1, parent2)]
            else:
                offspring[k] = [alpha * (p1 - p2) + p1 for p1, p2 in zip(parent1, parent2)]
            
        return offspring

    def SX_version1(self, parents, offspring_size):
        offspring = np.empty(offspring_size, dtype=parents.dtype)
        for k in range(offspring_size[0]):
            parent1_idx = k % parents.shape[0]
            parent2_idx = (k + 1) % parents.shape[0]
            parent1 = parents[parent1_idx]
            parent2 = parents[parent2_idx]
            
            child = [sqrt((p1 ** 2 + p2 ** 2) / 2) for p1, p2 in zip(parent1, parent2)]
            
            offspring[k] = child
            
        return offspring

    def SX_version2(self, parents, offspring_size):
        offspring = np.empty(offspring_size, dtype=parents.dtype)
        for k in range(offspring_size[0]):
            parent1_idx = k % parents.shape[0]
            parent2_idx = (k + 1) % parents.shape[0]
            parent1 = parents[parent1_idx]
            parent2 = parents[parent2_idx]
            
            alpha = random.uniform(0, 1)
            
            child = [sqrt(alpha * p1 ** 2 + (1 - alpha) * p2 ** 2) for p1, p2 in zip(parent1, parent2)]
            
            offspring[k] = child
        return offspring

    def f1_PAX(self, parents, offspring_size):
        offspring = np.empty(offspring_size, dtype=parents.dtype)
        for k in range(offspring_size[0]):
            parent1_idx = k % parents.shape[0]
            parent2_idx = (k + 1) % parents.shape[0]
            parent1 = parents[parent1_idx]
            parent2 = parents[parent2_idx]
            
            size = len(parent1)
            cp = random.randint(0, size - 1)
            
            child1 = parent1.copy()
            child2 = parent2.copy()
            
            child1[cp] = (parent1[cp] + parent2[cp]) / 2
            child2[cp] = (parent1[cp] + parent2[cp]) / 2
            
            offspring[k] = child1 if k % 2 == 0 else child2
            
        return offspring

    #TODO krzyzowanie Wojtka (:

    def crossover(self, parents, offspring_size):
        if self.original_crossover_type  == "arithmetic":
            print("jestem tu")
            return self.arithmetic_crossover(parents, offspring_size)
        elif self.original_crossover_type  == "linear":
            return self.linear_crossover(parents, offspring_size)
        elif self.original_crossover_type  == "alpha_mixed":
            return self.alpha_mixed_crossover(parents, offspring_size)
        elif self.original_crossover_type  == "alpha_beta_mixed":
            return self.alpha_beta_mixed_crossover(parents, offspring_size)
        elif self.original_crossover_type  == "average":
            return self.average_crossover(parents, offspring_size)
        elif self.original_crossover_type  == "crossover_HX":
            return self.crossover_HX(parents, offspring_size)
        elif self.original_crossover_type  == "SX_version1":
            return self.SX_version1(parents, offspring_size)
        elif self.original_crossover_type  == "SX_version2":
            return self.SX_version2(parents, offspring_size)
        elif self.original_crossover_type  == "f1_PAX":
            return self.f1_PAX(parents, offspring_size)
        # elif self.crossover_type == "fitness_weighted_cross_for_real_numbers":
        #     return self.fitness_weighted_cross_for_real_numbers(parents, offspring_size)
        else:
            return super().crossover(parents, offspring_size)
        
    def evaluate_subject(self, subject):
        return sum(subject)
        
    #TODO mutacja Gaussa