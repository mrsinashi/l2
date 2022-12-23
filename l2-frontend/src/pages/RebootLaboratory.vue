<template>
  <div class="box card-1 card-no-hover">
    <h5 class="text-center">
      Перезагрузка анализаторов
    </h5>
    Выберите анализатор:
    <select v-model="selectedAnalyzer">
      <option
        v-for="item in analyzers.data"
        :key="item.pk"
        :value="item.title"
      >
        {{ item.title }}
      </option>
    </select>
    <div class="button">
      <Input
        style="margin-right: 5px"
        type="button"
        value="Перезагрузить"
        @click="rebootAnalyzer"
      />
    </div>
  </div>
</template>

<script lang="ts">

export default {
  name: 'RebootLab',
  data() {
    return {
      analyzers: {},
      selectedAnalyzer: '',
    };
  },
  mounted() {
    this.getAnalyzers();
  },
  methods: {
    async rebootAnalyzer2() {
      await fetch('http://192.168.50.253:9185', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ service_name: this.selectedAnalyzer, action: 'restart', api_key: 'hg9AkQNWb8M' }),
      });
    },
    async getAnalyzers() {
      this.analyzers = await this.$api('get-analyzers');
    },
    async rebootAnalyzer() {
      await this.$api('reboot-analyzer', [this.selectedAnalyzer]);
    },
  },
};
</script>

<style scoped>
.box {
  background-color: #FFF;
  margin: 10px 10px;
  flex-basis: 350px;
  flex-grow: 1;
  border-radius: 4px;
  min-height: 840px;
}
.main {
  display: flex;
  flex-wrap: wrap;
}
.scroll {
  overflow-y: auto;
  max-height: 790px;
}
.title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-left: 9px;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.border {
  border: 1px solid #ddd;
}
.button {
  display: flex;
  justify-content: flex-end;
}
</style>
