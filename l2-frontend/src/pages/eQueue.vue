<template>
  <div>
    {{ name }}
    <FormulateInput
    type="select"
    name="cabinetid"
    label="Кабинет"
    />
    <FormulateInput
    type="text"
    name="priority"
    label="Приоритет"
    placeholder="Проритет в очереди"
    validation="number"
    inputmode="numeric"
    pattern="[0-9]*"
    maxlength="2"
    />
    <FormulateInput
    type="submit"
    label="Добавить"
    />
  </div>
</template>

<script lang="ts">
export default {
  name: 'Equeues',
  data() {
    return {
      name: 'Электронная очередь',
    };
  },
  methods: {
    msg() {
      this.name = 'Очередь';
    },
  },
};
</script>

<style lang="scss" scoped>

</style>
