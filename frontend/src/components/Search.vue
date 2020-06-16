<template>
  <b-container>
    <b-row
      :class="[
        'justify-content-center',
        gotQueryResults == false && 'h-100 align-items-center'
      ]"
    >
      <b-col>
        <b-input-group class="mt-3">
          <b-input-group-prepend>
            <b-dropdown :text="defaultDataset" variant="warning">
              <b-dropdown-item
                v-for="dataset in this.datasets"
                :key="dataset"
                @click="defaultDataset = dataset"
                >{{ dataset }}</b-dropdown-item
              >
            </b-dropdown>
          </b-input-group-prepend>

          <transition name="fade">
            <b-form-input
              size="lg"
              v-model="inputData"
              @update="cleanResultsOnInputChange"
              required
            />
          </transition>

          <b-input-group-append>
            <b-button @click="sendQuery" variant="warning">Search</b-button>
          </b-input-group-append>
        </b-input-group>
      </b-col>
    </b-row>

    <b-row v-for="filename in this.results" :key="filename">
      <b-col md="10">
        <b-card class="mt-3 text-center">
          <b-card-text>{{ filename }}</b-card-text>
        </b-card>
      </b-col>
      <b-col md="auto">
        <b-button
          class="mt-4"
          variant="success"
          @click="exposeFileToPublic(filename)"
          >Download</b-button
        >
      </b-col>
    </b-row>

    <div
      v-if="gotQueryResults == true && Object.keys(results).length == 0"
      class="text-center mt-3"
    >
      <h2>
        There are not any results for such query...
      </h2>
    </div>

    <div v-if="gotQueryResults == true" class="statistics">
      <br />
      Parsed (possibly simplified) query (DNF): {{ this.query }} <br />Time:
      {{ this.time }} s
    </div>
  </b-container>
</template>

<style>
* {
  outline: none;
  outline-style: none;
}
.statistics {
  color: gray;
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.5s ease-in-out, transform 0.5 ease;
}
.fade-enter,
.fade-leave-to {
  opacity: 0;
}

.fade-enter-to,
.fade-leave {
  opacity: 1;
}
</style>

<script>
import axios from "axios";

export default {
  data() {
    return {
      inputData: "",
      gotQueryResults: false,
      datasets: [],
      defaultDataset: "",
      results: {}
    };
  },
  created() {
    this.datasetNames();
  },
  methods: {
    searchBarIsNotEmpty() {
      if (this.inputData != "") {
        return true;
      }

      this.$toast.open({
        message: "Search bar cannot be empty!",
        type: "warning",
        position: "top",
        duration: 5000
      });

      return false;
    },
    sendQuery() {
      if (this.searchBarIsNotEmpty()) {
        axios
          .get(
            `${process.env.VUE_APP_BASE_URL ||
              "https://kcgusgone6.execute-api.eu-central-1.amazonaws.com/devel"}/query/${
              this.defaultDataset
            }/${this.inputData}`
          )
          .then(response => {
            this.gotQueryResults = true;
            this.results = response.data["data"];
            this.time = response.data["time"];
            this.query = response.data["query"];
          })
          .catch(error => {
            this.$toast.open({
              message: error.response ? error.response.data : error.message,
              type: "error",
              position: "top",
              duration: 5000
            });
          });
      }
    },
    datasetNames() {
      axios
        .get(
          `${process.env.VUE_APP_BASE_URL ||
            "https://kcgusgone6.execute-api.eu-central-1.amazonaws.com/devel"}/dataset_names`
        )
        .then(response => {
          console.log(response.data);
          this.datasets = response.data;
          this.defaultDataset = this.datasets[0];
        })
        .catch(error => {
          this.$toast.open({
            message: error.response ? error.response.data : error.message,
            type: "error",
            position: "top-right",
            duration: 5000
          });
          this.datasets = [];
        });
    },
    cleanResultsOnInputChange() {
      this.gotQueryResults = false;
      this.results = [];
    },
    exposeFileToPublic(filename) {
      axios
        .get(
          `${process.env.VUE_APP_BASE_URL ||
            "https://kcgusgone6.execute-api.eu-central-1.amazonaws.com/devel"}/publish_file/${
            this.defaultDataset
          }/${filename}`
        )
        .then(response => {
          window.open(response.data, "_blank");
        })
        .catch(error => {
          this.$toast.open({
            message: error.response ? error.response.data : error.message,
            type: "error",
            position: "top",
            duration: 5000
          });
        });
    }
  }
};
</script>
